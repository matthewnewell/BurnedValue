"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ── EVM calculation fixtures ──────────────────────────────────────────────────

@pytest.fixture
def simple_project():
    """Minimal project dict for testing EVM calculations."""
    return {
        'id': 'test-project',
        'name': 'Test Project',
        'bac': 100000.0,
        'baseline_scope': 100.0,
        'start_date': '2026-01-01',
        'end_date': '2026-06-30',
        'interval_unit': 'weeks',
        'interval_size': 2,
    }


@pytest.fixture
def single_period():
    """One completed period — 50 points done, $45k spent."""
    return [{
        'period_id': 'p1',
        'date': '2026-01-15',
        'actual_cost': 45000.0,
        'points_completed': 50.0,
        'scope_delta': 0.0,
    }]


@pytest.fixture
def two_periods():
    """Two periods with scope creep in the second."""
    return [
        {
            'period_id': 'p1',
            'date': '2026-01-15',
            'actual_cost': 20000.0,
            'points_completed': 25.0,
            'scope_delta': 0.0,
        },
        {
            'period_id': 'p2',
            'date': '2026-01-29',
            'actual_cost': 25000.0,
            'points_completed': 20.0,
            'scope_delta': 20.0,  # scope grew by 20 points
        },
    ]


# ── Flask app fixtures (for integration tests) ────────────────────────────────

@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask test application with fully isolated data directory.

    Patches utils.DATA_FILE and utils._DATA_DIR so JSON storage writes
    to a per-test temp directory, not the real data/ folder.
    SQLite is redirected to the same temp dir via SQLALCHEMY_DATABASE_URI.
    """
    import utils
    import app as flask_app

    data_file = str(tmp_path / 'projects.json')
    db_file   = str(tmp_path / 'burnedvalue.db')

    monkeypatch.setattr(utils, 'DATA_FILE', data_file)
    monkeypatch.setattr(utils, '_DATA_DIR', str(tmp_path))

    flask_app.app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_file}',
    })

    from db import db
    with flask_app.app.app_context():
        db.create_all()

    yield flask_app.app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
