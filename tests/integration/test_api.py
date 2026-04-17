"""
Integration tests for Flask API routes.

Stubs — to be fleshed out as routes are built.
See app.py for current routes.
"""
import pytest


class TestProjectRoutes:

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_index_returns_200(self, client):
        response = client.get('/')
        assert response.status_code == 200

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_create_project_get(self, client):
        response = client.get('/create')
        assert response.status_code == 200

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_create_project_post(self, client):
        response = client.post('/create', data={
            'name': 'Test Project',
            'bac': '100000',
            'start_date': '2026-01-01',
            'end_date': '2026-06-30',
        })
        assert response.status_code in (200, 302)

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_dashboard_returns_200(self, client):
        pass

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_bluf_returns_200(self, client):
        pass


class TestProjectApiEndpoint:

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_api_project_returns_json(self, client):
        pass

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_api_project_contains_periods(self, client):
        pass


class TestDemoProject:

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_demo_project_loads(self, client):
        response = client.get('/dashboard/demo')
        assert response.status_code == 200

    @pytest.mark.skip(reason="Integration test setup not yet configured")
    def test_demo_reset_restores_seed(self, client):
        """Reset should restore demo to original seed state."""
        pass


class TestPhase1Routes:
    """Stubs for Epic/Feature/Story routes — Phase 1."""

    @pytest.mark.skip(reason="Phase 1 — not yet implemented")
    def test_epics_list(self, client):
        pass

    @pytest.mark.skip(reason="Phase 1 — not yet implemented")
    def test_create_epic(self, client):
        pass

    @pytest.mark.skip(reason="Phase 1 — not yet implemented")
    def test_features_list(self, client):
        pass

    @pytest.mark.skip(reason="Phase 1 — not yet implemented")
    def test_create_story(self, client):
        pass

    @pytest.mark.skip(reason="Phase 1 — not yet implemented")
    def test_update_story_status(self, client):
        pass


class TestPhase2Routes:
    """Stubs for cost report entry routes — Phase 2."""

    @pytest.mark.skip(reason="Phase 2 — not yet implemented")
    def test_cost_report_entry(self, client):
        pass

    @pytest.mark.skip(reason="Phase 2 — not yet implemented")
    def test_iteration_close(self, client):
        pass
