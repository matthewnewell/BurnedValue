import os
from dotenv import load_dotenv
load_dotenv()  # loads .env for local dev; no-op in GAE/Docker where env vars are set directly

# ai_client is imported AFTER load_dotenv so it picks up .env values at module level
import ai_client

from flask import Flask, render_template, request, redirect, url_for, jsonify, abort, session
from models import CalculationEngine, Period
import utils
import uuid
import json
from datetime import datetime

app = Flask(__name__)
# Set SECRET_KEY env var in production. The default is fine for local dev.
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

@app.template_filter('fmtdate')
def fmtdate(value):
    """Convert yyyy-mm-dd to mm-dd-yyyy for display."""
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%m-%d-%Y')
    except (ValueError, TypeError):
        return value


# ── Session-aware helpers for demo project ─────────────────────────────────────

def get_project_for_request(project_id):
    """
    For real projects: load from file.
    For the demo: start from the canonical seed, then overlay any fields
    the current visitor has edited (stored in their session cookie).
    """
    if project_id == 'demo':
        project = utils.get_canonical_demo()
        overrides = session.get('demo_overrides', {})
        # Invalidate stale session overrides when the seed version changes
        if overrides.get('_seed_version') != project.get('_seed_version'):
            session.pop('demo_overrides', None)
            overrides = {}
        project.update(overrides)
        return project
    return utils.get_project(project_id)


# Fields that visitors are allowed to override on the demo project
_DEMO_MUTABLE_FIELDS = [
    'name', 'description', 'contract_value', 'bac',
    'start_date', 'end_date', 'interval_unit', 'interval_size',
    'baseline_scope', 'periods'
]

def save_project_for_request(project_id, project):
    """
    For real projects: write to file.
    For the demo: store only the mutable fields in the session cookie so
    the canonical seed is never touched and other visitors are unaffected.
    """
    if project_id == 'demo':
        overrides = {k: project[k] for k in _DEMO_MUTABLE_FIELDS if k in project}
        overrides['_seed_version'] = project.get('_seed_version')
        session['demo_overrides'] = overrides
        session.modified = True
    else:
        utils.save_project_data(project_id, project)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    utils.ensure_demo_project()
    projects_dict = utils.load_projects()
    projects_list = []
    for p in projects_dict.values():
        # For the demo shown on the index, always use the canonical version
        # (visitor's session edits only affect the dashboard view)
        metrics = CalculationEngine.compute_metrics(p, p.get('periods', []))
        projects_list.append({**p, 'metrics': metrics})
    projects_list.sort(key=lambda p: (0 if p.get('is_demo') else 1, p.get('name', '')))
    return render_template('index.html', projects=projects_list)


@app.route('/create', methods=['GET', 'POST'])
def create_project():
    if request.method == 'POST':
        project_id = str(uuid.uuid4())
        cv_raw = request.form.get('contract_value', '').strip()
        data = {
            "id": project_id,
            "name": request.form['name'],
            "description": request.form.get('description', ''),
            "contract_value": float(cv_raw) if cv_raw else None,
            "bac": float(request.form['bac']),
            "start_date": request.form['start_date'],
            "end_date": request.form['end_date'],
            "interval_unit": request.form.get('interval_unit', 'weeks'),
            "interval_size": int(request.form.get('interval_size', 2)),
            "periods": []
        }
        utils.save_project_data(project_id, data)
        return redirect(url_for('dashboard', project_id=project_id))
    return render_template('create_project.html')


@app.route('/project/<project_id>/update', methods=['GET', 'POST'])
def update_project(project_id):
    project = get_project_for_request(project_id)
    if not project:
        abort(404)

    if request.method == 'POST':
        cv_raw = request.form.get('contract_value', '').strip()
        project['name']           = request.form['name']
        project['description']    = request.form.get('description', '')
        project['contract_value'] = float(cv_raw) if cv_raw else None
        project['bac']            = float(request.form['bac'])
        project['start_date']     = request.form['start_date']
        project['end_date']       = request.form['end_date']
        # interval_unit and interval_size are intentionally not updated here —
        # changing cadence after data exists would misalign period records
        save_project_for_request(project_id, project)
        return redirect(url_for('dashboard', project_id=project_id))

    return render_template('update_project.html', project=project)


@app.route('/dashboard/<project_id>')
def dashboard(project_id):
    project = get_project_for_request(project_id)
    if not project:
        return "Project not found", 404

    periods = project.get('periods', [])
    metrics = CalculationEngine.compute_metrics(project, periods)
    narrative = CalculationEngine.generate_narrative(project, periods, metrics)
    period_details = CalculationEngine.compute_period_details(project, periods)

    baseline_scope = project.get('baseline_scope') or 0
    scope_growth = round(metrics['total_scope'] - baseline_scope, 1) if metrics['total_scope'] else 0

    # Build interval list and annotate each with matching period data (if any)
    intervals = utils.generate_intervals(project)
    periods_by_date = {p['date']: p for p in periods}
    for iv in intervals:
        iv['period'] = periods_by_date.get(iv['date'])

    return render_template(
        'dashboard.html',
        project=project,
        metrics=metrics,
        narrative=narrative,
        period_details=period_details,
        baseline_scope=baseline_scope,
        scope_growth=scope_growth,
        intervals=intervals
    )


@app.route('/project/<project_id>/add_period', methods=['GET', 'POST'])
def add_period(project_id):
    project = get_project_for_request(project_id)
    if not project:
        abort(404)

    if request.method == 'POST':
        scope_delta = float(request.form.get('scope_delta', 0) or 0)

        if not project['periods']:
            # First period: the user enters the baseline directly
            baseline = float(request.form.get('baseline_scope', 0) or 0)
            project['baseline_scope'] = baseline
            scope_delta = 0.0
            total_scope = baseline
        else:
            prev_total = project['periods'][-1]['total_estimated_effort']
            total_scope = prev_total + scope_delta

        period = Period(
            date=request.form['date'],
            points_completed=float(request.form['points']),
            labor_hours=float(request.form.get('labor_hours', 0)),
            labor_rate=float(request.form.get('labor_rate', 0)),
            non_labor_cost=float(request.form.get('non_labor', 0)),
            total_scope=total_scope,
            scope_delta=scope_delta
        )
        project['periods'].append(period.to_dict())
        save_project_for_request(project_id, project)
        return redirect(url_for('dashboard', project_id=project_id))

    # Compute context for the scope governance section
    baseline_scope = project.get('baseline_scope')
    has_periods = bool(project['periods'])
    prior_growth = sum(p.get('scope_delta', 0) for p in project['periods'])
    current_total = (baseline_scope or 0) + prior_growth

    prefill_date = request.args.get('date', '')

    return render_template(
        'entry.html',
        project=project,
        baseline_scope=baseline_scope,
        has_periods=has_periods,
        prior_growth=prior_growth,
        current_total=current_total,
        prefill_date=prefill_date
    )


@app.route('/project/<project_id>/edit_period/<period_id>', methods=['GET', 'POST'])
def edit_period(project_id, period_id):
    project = get_project_for_request(project_id)
    if not project:
        abort(404)

    period_data = next((p for p in project['periods'] if p.get('period_id') == period_id), None)
    if not period_data:
        abort(404)

    if request.method == 'POST':
        scope_delta = float(request.form.get('scope_delta', 0) or 0)

        # Recompute total_scope for this period: baseline + sum of all other deltas + this delta
        baseline = project.get('baseline_scope', 0.0)
        other_deltas = sum(
            p.get('scope_delta', 0) for p in project['periods']
            if p.get('period_id') != period_id
               and p['date'] <= period_data['date']   # only periods up to this one
        )
        total_scope = baseline + other_deltas + scope_delta

        updated = Period(
            date=request.form['date'],
            points_completed=float(request.form['points']),
            labor_hours=float(request.form.get('labor_hours', 0)),
            labor_rate=float(request.form.get('labor_rate', 0)),
            non_labor_cost=float(request.form.get('non_labor', 0)),
            total_scope=total_scope,
            scope_delta=scope_delta,
            period_id=period_id
        )
        idx = next(i for i, p in enumerate(project['periods']) if p.get('period_id') == period_id)
        project['periods'][idx] = updated.to_dict()

        # Recompute total_estimated_effort for all periods after a delta change
        utils.recompute_scope(project)
        save_project_for_request(project_id, project)
        return redirect(url_for('dashboard', project_id=project_id))

    # Compute context for scope governance section
    baseline_scope = project.get('baseline_scope', 0.0)
    prior_growth = sum(
        p.get('scope_delta', 0) for p in project['periods']
        if p.get('period_id') != period_id
    )
    period_scope_delta = period_data.get('scope_delta', 0.0)

    return render_template(
        'edit_period.html',
        project=project,
        period=period_data,
        baseline_scope=baseline_scope,
        prior_growth=prior_growth,
        period_scope_delta=period_scope_delta
    )


@app.route('/project/<project_id>/delete_period/<period_id>', methods=['POST'])
def delete_period(project_id, period_id):
    project = get_project_for_request(project_id)
    if not project:
        abort(404)
    project['periods'] = [p for p in project['periods'] if p.get('period_id') != period_id]
    save_project_for_request(project_id, project)
    return redirect(url_for('dashboard', project_id=project_id))


@app.route('/project/<project_id>/bluf')
def bluf(project_id):
    project = get_project_for_request(project_id)
    if not project:
        abort(404)
    periods  = project.get('periods', [])
    metrics  = CalculationEngine.compute_metrics(project, periods)
    bluf_data = CalculationEngine.generate_bluf(project, periods, metrics)
    return render_template('bluf.html', project=project, metrics=metrics, bluf=bluf_data, now=datetime.now())


@app.route('/demo/reset', methods=['POST'])
def reset_demo():
    """Clear this visitor's session edits, restoring the demo to its initial state."""
    session.pop('demo_overrides', None)
    session.modified = True
    return redirect(url_for('dashboard', project_id='demo'))


@app.route('/project/<project_id>/delete', methods=['POST'])
def delete_project(project_id):
    project = utils.get_project(project_id)
    if not project:
        abort(404)
    if project.get('is_demo'):
        abort(403)
    utils.delete_project(project_id)
    return redirect(url_for('index'))


@app.route('/api/project/<project_id>')
def project_api(project_id):
    project = get_project_for_request(project_id)
    return jsonify(project)


@app.route('/project/<project_id>/chat', methods=['POST'])
def project_chat(project_id):
    """AI chat endpoint — receives conversation history, returns AI reply."""
    project = get_project_for_request(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    body     = request.get_json(force=True)
    messages = body.get("messages", [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    # Build rich project context for the AI
    periods  = project.get("periods", [])
    metrics  = CalculationEngine.compute_metrics(project, periods)
    details  = CalculationEngine.compute_period_details(project, periods)

    context = {
        "name":           project.get("name"),
        "description":    project.get("description"),
        "bac":            project.get("bac"),
        "contract_value": project.get("contract_value"),
        "start_date":     project.get("start_date"),
        "end_date":       project.get("end_date"),
        "baseline_scope": project.get("baseline_scope"),
        "metrics":        metrics,
        "periods":        periods,
        "period_details": details,
    }

    system = f"""You are an expert project governance analyst embedded in the Burned Value dashboard.
Burned Value combines EVMS (Earned Value Management) with Agile Release Burndown.

Key concepts:
- CPI (Cost Performance Index): EV / AC. <1.0 = over budget, >1.0 = under budget.
- SPI (Schedule Performance Index): EV / PV. <1.0 = behind schedule.
- EAC (Estimate at Completion): projected final cost.
- Scope Coverage Ratio: Baseline Scope / Current Total Scope × 100%. 100% = scope unchanged; below 100% means scope grew without a budget increase (uncompensated scope growth). ≥90% green, 70-89% yellow, <70% red.
- budget_per_point: BAC / Total Scope Points (non-display field, used internally for $/pt calculations).
- Percent Complete: Completed Points / Total Scope Points.

Current project data (JSON):
{json.dumps(context, indent=2, default=str)}

Answer the operator's questions about this project clearly and concisely.
Use specific numbers from the data. Flag risks proactively.
When asked to update data, describe exactly what change you would make — data write capability is coming soon."""

    reply = ai_client.chat(messages=messages, system=system)
    return jsonify({"reply": reply, "provider": ai_client.AI_PROVIDER})


if __name__ == '__main__':
    app.run(debug=True)
