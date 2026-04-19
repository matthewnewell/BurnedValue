import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from filelock import FileLock

_DATA_DIR = os.environ.get('DATA_DIR', 'data')
DATA_FILE = os.path.join(_DATA_DIR, 'projects.json')
_PORTFOLIO_FILE = os.path.join(_DATA_DIR, 'portfolio.json')

_PORTFOLIO_DEFAULTS = {
    "name": "Burned Value",
    "description": "",
}


def get_portfolio():
    """Load portfolio config. Returns defaults if file doesn't exist."""
    if not os.path.exists(_PORTFOLIO_FILE):
        return dict(_PORTFOLIO_DEFAULTS)
    with open(_PORTFOLIO_FILE) as f:
        data = json.load(f)
    return {**_PORTFOLIO_DEFAULTS, **data}


def save_portfolio(data):
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_PORTFOLIO_FILE, 'w') as f:
        json.dump(data, f, indent=2)

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
            {"period_id": pids[0], "date": d(2),  "scope_delta":  0, "points_completed": 32, "labor_hours": 360, "labor_rate": 40, "non_labor_cost": 1600, "actual_cost": 16000},
            {"period_id": pids[1], "date": d(4),  "scope_delta":  0, "points_completed": 28, "labor_hours": 360, "labor_rate": 40, "non_labor_cost": 1600, "actual_cost": 16000},
            # Scope creep +40 — VD steps down, costs rise, team absorbs it
            {"period_id": pids[2], "date": d(6),  "scope_delta": 40, "points_completed": 22, "labor_hours": 460, "labor_rate": 40, "non_labor_cost": 3600, "actual_cost": 22000},
            # Scope creep +70 — VD drops sharply to $806/pt; cumulative cpp still under
            {"period_id": pids[3], "date": d(8),  "scope_delta": 70, "points_completed": 20, "labor_hours": 420, "labor_rate": 40, "non_labor_cost": 3200, "actual_cost": 20000},
            {"period_id": pids[4], "date": d(10), "scope_delta":  0, "points_completed": 22, "labor_hours": 420, "labor_rate": 40, "non_labor_cost": 3200, "actual_cost": 20000},
            # Final scope hit +15 — VD drops to $769/pt; cumulative cpp ($793) tips above it → red bar
            {"period_id": pids[5], "date": d(12), "scope_delta": 15, "points_completed": 21, "labor_hours": 440, "labor_rate": 40, "non_labor_cost": 3400, "actual_cost": 21000},
        ]
    }


_SAMPLE_PERIOD_IDS = [f"sample-p{i}" for i in range(1, 10)]


def _build_sample_project():
    today = datetime.now().date()
    year  = today.year
    start = datetime(year, 1, 5).date()
    end   = datetime(year, 8, 31).date()

    def d(weeks_from_start):
        return (start + timedelta(weeks=weeks_from_start)).isoformat()

    pids = _SAMPLE_PERIOD_IDS
    # Each period: costs well below earned value, velocity ahead of planned pace.
    # BAC $180k, baseline_scope 120 pts → budget_per_point = $1,500/pt
    # 64 pts completed at ~68.7% through the schedule → SPI ≈ 1.51, CPI ≈ 1.16
    return {
        "id": "sample-1",
        "is_sample": True,
        "_seed_version": 1,
        "name": "Sentinel Analytics Platform",
        "description": "Sample project — delivering a real-time security telemetry platform ahead of schedule and under budget.",
        "contract_value": 210000.0,
        "bac": 180000.0,
        "start_date": start.isoformat(),
        "end_date":   end.isoformat(),
        "interval_unit": "weeks",
        "interval_size": 2,
        "baseline_scope": 120.0,
        "periods": [
            # labor: hours * rate; non_labor added; actual_cost stored explicitly
            {"period_id": pids[0], "date": d(2),  "scope_delta": 0, "points_completed": 10, "labor_hours": 280, "labor_rate": 40, "non_labor_cost": 1800, "actual_cost": 13000},
            {"period_id": pids[1], "date": d(4),  "scope_delta": 0, "points_completed": 11, "labor_hours": 320, "labor_rate": 40, "non_labor_cost": 1700, "actual_cost": 14500},
            {"period_id": pids[2], "date": d(6),  "scope_delta": 0, "points_completed": 10, "labor_hours": 280, "labor_rate": 40, "non_labor_cost": 1800, "actual_cost": 13000},
            {"period_id": pids[3], "date": d(8),  "scope_delta": 0, "points_completed": 12, "labor_hours": 340, "labor_rate": 40, "non_labor_cost": 1400, "actual_cost": 15000},
            {"period_id": pids[4], "date": d(10), "scope_delta": 0, "points_completed": 11, "labor_hours": 305, "labor_rate": 40, "non_labor_cost": 1800, "actual_cost": 14000},
            {"period_id": pids[5], "date": d(12), "scope_delta": 0, "points_completed": 10, "labor_hours": 280, "labor_rate": 40, "non_labor_cost": 1800, "actual_cost": 13000},
        ]
    }


def ensure_sample_project():
    projects = load_projects()
    current_version = projects.get('sample-1', {}).get('_seed_version')
    if current_version != _build_sample_project()['_seed_version']:
        projects['sample-1'] = _build_sample_project()
        save_projects(projects)


def get_canonical_sample():
    return _build_sample_project()


def _lock_path():
    return DATA_FILE + '.lock'


def load_projects():
    if not os.path.exists(DATA_FILE):
        return {}
    with FileLock(_lock_path()):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}


def save_projects(projects):
    data_dir = os.path.dirname(DATA_FILE)
    os.makedirs(data_dir, exist_ok=True)
    with FileLock(_lock_path()):
        fd, tmp_path = tempfile.mkstemp(dir=data_dir, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(projects, f, indent=4)
            os.replace(tmp_path, DATA_FILE)
        except Exception:
            os.unlink(tmp_path)
            raise


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
    current_version = projects.get('demo', {}).get('_seed_version')
    if current_version != _build_demo_project()['_seed_version']:
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
        try:
            project['baseline_scope'] = float(periods[0]['total_estimated_effort'])
        except KeyError:
            return changed
        changed = True

    prev = project['baseline_scope']
    for p in periods:
        if 'scope_delta' not in p:
            try:
                p['scope_delta'] = float(p['total_estimated_effort']) - prev
                prev = float(p['total_estimated_effort'])
            except KeyError:
                p['scope_delta'] = 0.0
                prev += 0.0
            changed = True
        else:
            prev += float(p['scope_delta'])

    return changed
