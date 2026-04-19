"""
Integration tests for Flask API routes.

Stubs — to be fleshed out as routes are built.
See app.py for current routes.
"""
import pytest


class TestProjectRoutes:

    def test_index_returns_200(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_create_project_get(self, client):
        response = client.get('/create')
        assert response.status_code == 200

    def test_create_project_post_redirects_to_dashboard(self, client):
        response = client.post('/create', data={
            'name': 'Test Project',
            'bac': '100000',
            'start_date': '2026-01-01',
            'end_date': '2026-06-30',
            'interval_unit': 'weeks',
            'interval_size': '2',
        })
        assert response.status_code == 302
        assert '/dashboard/' in response.headers['Location']

    def test_dashboard_returns_200(self, client):
        # Create a project first, then follow the redirect to its dashboard
        create = client.post('/create', data={
            'name': 'Dashboard Test',
            'bac': '50000',
            'start_date': '2026-01-01',
            'end_date': '2026-06-30',
            'interval_unit': 'weeks',
            'interval_size': '2',
        })
        dashboard_url = create.headers['Location']
        response = client.get(dashboard_url)
        assert response.status_code == 200

    def test_bluf_returns_200(self, client):
        create = client.post('/create', data={
            'name': 'BLUF Test',
            'bac': '50000',
            'start_date': '2026-01-01',
            'end_date': '2026-06-30',
            'interval_unit': 'weeks',
            'interval_size': '2',
        })
        project_id = create.headers['Location'].split('/dashboard/')[1]
        response = client.get(f'/project/{project_id}/bluf')
        assert response.status_code == 200


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
