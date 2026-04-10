import json
import os
import uuid
from datetime import datetime, timedelta

DATA_FILE = os.path.join('data', 'projects.json')

# Fixed period IDs so they survive demo rebuilds and session lookups stay stable
_DEMO_PERIOD_IDS = [f"demo-p{i}" for i in range(1, 10)]


def _build_demo_project():
    """
    Builds the demo project with dates relative to today.
    Period IDs are fixed strings so edit/delete routes remain stable
    across page loads regardless of date recalculation.
    """
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
        "bac": 250000.0,
        "start_date": start.isoformat(),
        "end_date":   end.isoformat(),
        "periods": [
            {"period_id": pids[0], "date": d(13), "points_completed": 25, "labor_hours": 500, "labor_rate": 40, "non_labor_cost": 5000,  "actual_cost": 25000, "total_estimated_effort": 200},
            {"period_id": pids[1], "date": d(11), "points_completed": 22, "labor_hours": 480, "labor_rate": 40, "non_labor_cost": 3000,  "actual_cost": 22200, "total_estimated_effort": 200},
            {"period_id": pids[2], "date": d(9),  "points_completed": 20, "labor_hours": 520, "labor_rate": 40, "non_labor_cost": 4000,  "actual_cost": 24800, "total_estimated_effort": 240},
            {"period_id": pids[3], "date": d(7),  "points_completed": 18, "labor_hours": 480, "labor_rate": 40, "non_labor_cost": 2000,  "actual_cost": 21200, "total_estimated_effort": 240},
            {"period_id": pids[4], "date": d(5),  "points_completed": 22, "labor_hours": 500, "labor_rate": 40, "non_labor_cost": 3500,  "actual_cost": 23500, "total_estimated_effort": 240},
            {"period_id": pids[5], "date": d(3),  "points_completed": 19, "labor_hours": 460, "labor_rate": 40, "non_labor_cost": 2000,  "actual_cost": 20400, "total_estimated_effort": 260},
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
    """Load a project from file. Backfills period_ids for legacy data."""
    projects = load_projects()
    project = projects.get(project_id)
    if project and _backfill_period_ids(project):
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
    """
    Overwrites the canonical demo in the JSON file with fresh dates.
    Each visitor's edits live in their session — the file is just the
    pristine starting state used to seed new sessions.
    """
    projects = load_projects()
    projects['demo'] = _build_demo_project()
    save_projects(projects)


def get_canonical_demo():
    """Returns a freshly computed demo project (no session overlay)."""
    return _build_demo_project()


def _backfill_period_ids(project):
    """
    Adds a period_id to any period that doesn't have one.
    Returns True if any changes were made (so callers can decide to save).
    """
    changed = False
    for p in project.get('periods', []):
        if 'period_id' not in p:
            p['period_id'] = str(uuid.uuid4())
            changed = True
    return changed
