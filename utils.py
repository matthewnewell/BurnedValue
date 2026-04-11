import json
import os
import uuid
from datetime import datetime, timedelta

_DATA_DIR = os.environ.get('DATA_DIR', 'data')
DATA_FILE = os.path.join(_DATA_DIR, 'projects.json')

_DEMO_PERIOD_IDS = [f"demo-p{i}" for i in range(1, 10)]


def _build_demo_project():
    today = datetime.now().date()
    year  = today.year
    start = datetime(year, 2, 1).date()
    end   = datetime(year, 7, 4).date()

    def d(weeks_from_start):
        return (start + timedelta(weeks=weeks_from_start)).isoformat()

    pids = _DEMO_PERIOD_IDS
    return {
        "id": "demo",
        "is_demo": True,
        "_seed_version": 7,
        "name": "Digital Transformation Initiative",
        "description": "Sample project — modernizing legacy billing infrastructure to cloud-native microservices.",
        "contract_value": 262000.0,
        "bac": 250000.0,
        "start_date": start.isoformat(),
        "end_date":   end.isoformat(),
        "interval_unit": "weeks",
        "interval_size": 2,
        "baseline_scope": 200.0,
        "periods": [
            # Strong start — efficient delivery, AC well below EV, cpp well under VD
            {"period_id": pids[0], "date": d(2),  "scope_delta":  0, "points_completed": 32, "labor_hours": 360, "labor_rate": 40, "non_labor_cost": 1600, "actual_cost": 16000, "total_estimated_effort": 200},
            {"period_id": pids[1], "date": d(4),  "scope_delta":  0, "points_completed": 28, "labor_hours": 360, "labor_rate": 40, "non_labor_cost": 1600, "actual_cost": 16000, "total_estimated_effort": 200},
            # Scope creep +40 — VD steps down, costs rise, team absorbs it
            {"period_id": pids[2], "date": d(6),  "scope_delta": 40, "points_completed": 22, "labor_hours": 460, "labor_rate": 40, "non_labor_cost": 3600, "actual_cost": 22000, "total_estimated_effort": 240},
            # Scope creep +70 — VD drops sharply to $806/pt; cumulative cpp still under
            {"period_id": pids[3], "date": d(8),  "scope_delta": 70, "points_completed": 20, "labor_hours": 420, "labor_rate": 40, "non_labor_cost": 3200, "actual_cost": 20000, "total_estimated_effort": 310},
            {"period_id": pids[4], "date": d(10), "scope_delta":  0, "points_completed": 22, "labor_hours": 420, "labor_rate": 40, "non_labor_cost": 3200, "actual_cost": 20000, "total_estimated_effort": 310},
            # Final scope hit +15 — VD drops to $769/pt; cumulative cpp ($793) tips above it → red bar
            {"period_id": pids[5], "date": d(12), "scope_delta": 15, "points_completed": 21, "labor_hours": 440, "labor_rate": 40, "non_labor_cost": 3400, "actual_cost": 21000, "total_estimated_effort": 325},
        ]
    }


def load_projects():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_projects(projects):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(projects, f, indent=4)


def get_project(project_id):
    projects = load_projects()
    project = projects.get(project_id)
    if project:
        changed = _backfill_period_ids(project)
        changed = _backfill_scope_deltas(project) or changed
        if changed:
            projects[project_id] = project
            save_projects(projects)
    return project


def save_project_data(project_id, project_data):
    projects = load_projects()
    projects[project_id] = project_data
    save_projects(projects)


def delete_project(project_id):
    projects = load_projects()
    projects.pop(project_id, None)
    save_projects(projects)


def ensure_demo_project():
    projects = load_projects()
    projects['demo'] = _build_demo_project()
    save_projects(projects)


def get_canonical_demo():
    return _build_demo_project()


def generate_intervals(project):
    """
    Returns a list of interval end-date strings (ISO) from project start to
    whichever comes first: project end date or today + one interval (so the
    next upcoming interval is always visible).

    Each entry: { 'date': 'yyyy-mm-dd', 'label': 'Interval N' }
    """
    try:
        start = datetime.strptime(project['start_date'], '%Y-%m-%d')
        end   = datetime.strptime(project['end_date'],   '%Y-%m-%d')
    except (ValueError, KeyError):
        return []

    unit = project.get('interval_unit', 'weeks')
    size = int(project.get('interval_size', 2))

    def step_fn(base, n):
        if unit == 'months':
            total_months = base.month - 1 + size * n
            year  = base.year + total_months // 12
            month = total_months % 12 + 1
            import calendar
            day = min(base.day, calendar.monthrange(year, month)[1])
            return base.replace(year=year, month=month, day=day)
        days = size * 7 if unit == 'weeks' else size
        return base + timedelta(days=days * n)

    intervals = []
    n = 1
    current = step_fn(start, n)
    while current <= end:
        intervals.append({'date': current.strftime('%Y-%m-%d'), 'label': f'Interval {n}'})
        n += 1
        current = step_fn(start, n)

    return intervals


def recompute_scope(project):
    """
    After any scope_delta change, recompute total_estimated_effort for all periods
    in chronological order: baseline + cumulative deltas.
    Mutates project['periods'] in place.
    """
    baseline = project.get('baseline_scope', 0.0)
    periods = sorted(project['periods'], key=lambda x: x['date'])
    running = baseline
    for p in periods:
        running += p.get('scope_delta', 0.0)
        p['total_estimated_effort'] = running


def _backfill_period_ids(project):
    changed = False
    for p in project.get('periods', []):
        if 'period_id' not in p:
            p['period_id'] = str(uuid.uuid4())
            changed = True
    return changed


def _backfill_scope_deltas(project):
    """
    Derives scope_delta and baseline_scope for projects that predate this field.
    baseline_scope = first period's total_estimated_effort.
    scope_delta per period = difference from the previous period's total.
    """
    changed = False
    periods = sorted(project.get('periods', []), key=lambda x: x['date'])
    if not periods:
        return changed

    if 'baseline_scope' not in project:
        project['baseline_scope'] = float(periods[0]['total_estimated_effort'])
        changed = True

    prev = project['baseline_scope']
    for p in periods:
        if 'scope_delta' not in p:
            p['scope_delta'] = float(p['total_estimated_effort']) - prev
            changed = True
        prev = float(p['total_estimated_effort'])

    return changed
