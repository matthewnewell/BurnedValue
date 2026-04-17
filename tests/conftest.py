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
def app():
    """Flask test application with temporary data directory."""
    import tempfile
    import app as flask_app

    with tempfile.TemporaryDirectory() as tmpdir:
        flask_app.app.config.update({
            'TESTING': True,
            'DATA_DIR': tmpdir,
        })
        yield flask_app.app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
