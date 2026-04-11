import json
import os
import uuid
from datetime import datetime, timedelta

DATA_FILE = os.path.join('data', 'projects.json')

_DEMO_PERIOD_IDS = [f"demo-p{i}" for i in range(1, 10)]


def _build_demo_project():
    today = datetime.now().date()
    start = today - timedelta(weeks=15)
    end   = today + timedelta(weeks=11)

    def d(weeks_ago):
        return (today - timedelta(weeks=weeks_ago)).isoformat()

    pids = _DEMO_PERIOD_IDS
    return {
        "id": "demo",
        "is_demo": True,
        "name": "Digital Transformation Initiative",
        "description": (
            "Modernizing legacy billing infrastructure to cloud-native microservices. "
            "This demo shows what happens when scope is added without funding — "
            "Value Density dilutes and CPI craters."
        ),
        "contract_value": 275000.0,
        "bac": 250000.0,
        "start_date": start.isoformat(),
        "end_date":   end.isoformat(),
        "baseline_scope": 200.0,
        "periods": [
            {"period_id": pids[0], "date": d(13), "scope_delta":  0, "points_completed": 25, "labor_hours": 500, "labor_rate": 40, "non_labor_cost": 5000,  "actual_cost": 25000, "total_estimated_effort": 200},
            {"period_id": pids[1], "date": d(11), "scope_delta":  0, "points_completed": 22, "labor_hours": 480, "labor_rate": 40, "non_labor_cost": 3000,  "actual_cost": 22200, "total_estimated_effort": 200},
            {"period_id": pids[2], "date": d(9),  "scope_delta": 40, "points_completed": 20, "labor_hours": 520, "labor_rate": 40, "non_labor_cost": 4000,  "actual_cost": 24800, "total_estimated_effort": 240},
            {"period_id": pids[3], "date": d(7),  "scope_delta":  0, "points_completed": 18, "labor_hours": 480, "labor_rate": 40, "non_labor_cost": 2000,  "actual_cost": 21200, "total_estimated_effort": 240},
            {"period_id": pids[4], "date": d(5),  "scope_delta":  0, "points_completed": 22, "labor_hours": 500, "labor_rate": 40, "non_labor_cost": 3500,  "actual_cost": 23500, "total_estimated_effort": 240},
            {"period_id": pids[5], "date": d(3),  "scope_delta": 20, "points_completed": 19, "labor_hours": 460, "labor_rate": 40, "non_labor_cost": 2000,  "actual_cost": 20400, "total_estimated_effort": 260},
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
