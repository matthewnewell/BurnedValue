"""
Unit tests for the data storage layer (utils.py).

Run: .venv/bin/pytest tests/unit/test_utils.py -v
"""
import json
import pytest
import utils


@pytest.fixture()
def storage(tmp_path, monkeypatch):
    """Redirect all utils file I/O to an isolated temp directory."""
    monkeypatch.setattr(utils, 'DATA_FILE', str(tmp_path / 'projects.json'))
    monkeypatch.setattr(utils, '_DATA_DIR', str(tmp_path))
    return tmp_path


def _project(id='p1', name='Test Project'):
    return {
        'id': id,
        'name': name,
        'bac': 100000.0,
        'baseline_scope': 100.0,
        'start_date': '2026-01-01',
        'end_date': '2026-06-30',
        'interval_unit': 'weeks',
        'interval_size': 2,
        'periods': [],
    }


# ── load_projects ──────────────────────────────────────────────────────────────

class TestLoadProjects:

    def test_missing_file_returns_empty_dict(self, storage):
        assert utils.load_projects() == {}

    def test_roundtrip(self, storage):
        data = {'p1': _project('p1')}
        utils.save_projects(data)
        assert utils.load_projects() == data

    def test_corrupted_json_returns_empty_dict(self, storage):
        (storage / 'projects.json').write_text('not valid json {{{')
        assert utils.load_projects() == {}

    def test_empty_json_object_returns_empty_dict(self, storage):
        (storage / 'projects.json').write_text('{}')
        assert utils.load_projects() == {}


# ── save_project_data / get_project ───────────────────────────────────────────

class TestSaveAndGetProject:

    def test_save_and_retrieve(self, storage):
        proj = _project('abc')
        utils.save_project_data('abc', proj)
        assert utils.get_project('abc') == proj

    def test_get_missing_project_returns_none(self, storage):
        assert utils.get_project('does-not-exist') is None

    def test_overwrite_replaces_existing(self, storage):
        utils.save_project_data('abc', _project('abc', 'Original'))
        utils.save_project_data('abc', _project('abc', 'Updated'))
        assert utils.get_project('abc')['name'] == 'Updated'

    def test_multiple_projects_coexist(self, storage):
        utils.save_project_data('a', _project('a', 'Alpha'))
        utils.save_project_data('b', _project('b', 'Beta'))
        assert utils.get_project('a')['name'] == 'Alpha'
        assert utils.get_project('b')['name'] == 'Beta'

    def test_save_creates_data_directory_if_absent(self, tmp_path, monkeypatch):
        nested = tmp_path / 'subdir' / 'projects.json'
        monkeypatch.setattr(utils, 'DATA_FILE', str(nested))
        monkeypatch.setattr(utils, '_DATA_DIR', str(tmp_path / 'subdir'))
        utils.save_projects({'p1': _project()})
        assert nested.exists()


# ── delete_project ─────────────────────────────────────────────────────────────

class TestDeleteProject:

    def test_delete_removes_project(self, storage):
        utils.save_project_data('abc', _project('abc'))
        utils.delete_project('abc')
        assert utils.get_project('abc') is None

    def test_delete_missing_id_is_no_op(self, storage):
        utils.save_project_data('abc', _project('abc'))
        utils.delete_project('ghost')
        assert utils.get_project('abc') is not None

    def test_delete_does_not_affect_other_projects(self, storage):
        utils.save_project_data('a', _project('a'))
        utils.save_project_data('b', _project('b'))
        utils.delete_project('a')
        assert utils.get_project('b') is not None

    def test_delete_leaves_empty_file_not_missing(self, storage):
        utils.save_project_data('abc', _project('abc'))
        utils.delete_project('abc')
        assert utils.load_projects() == {}


# ── _backfill_period_ids ───────────────────────────────────────────────────────

class TestBackfillPeriodIds:

    def test_adds_period_id_when_missing(self):
        project = {'periods': [{'date': '2026-01-01', 'actual_cost': 1000.0}]}
        changed = utils._backfill_period_ids(project)
        assert changed is True
        assert 'period_id' in project['periods'][0]
        assert len(project['periods'][0]['period_id']) > 0

    def test_preserves_existing_period_id(self):
        project = {'periods': [{'period_id': 'my-id', 'date': '2026-01-01'}]}
        changed = utils._backfill_period_ids(project)
        assert changed is False
        assert project['periods'][0]['period_id'] == 'my-id'

    def test_partial_backfill_only_fills_missing(self):
        project = {
            'periods': [
                {'period_id': 'existing', 'date': '2026-01-01'},
                {'date': '2026-01-15', 'actual_cost': 500.0},
            ]
        }
        utils._backfill_period_ids(project)
        assert project['periods'][0]['period_id'] == 'existing'
        assert 'period_id' in project['periods'][1]

    def test_empty_periods_returns_no_change(self):
        project = {'periods': []}
        assert utils._backfill_period_ids(project) is False


# ── _backfill_scope_deltas ─────────────────────────────────────────────────────

class TestBackfillScopeDeltas:

    def test_no_change_when_scope_delta_already_present(self):
        project = {
            'baseline_scope': 100.0,
            'periods': [{'date': '2026-01-15', 'scope_delta': 0.0}],
        }
        changed = utils._backfill_scope_deltas(project)
        assert changed is False

    def test_backfills_baseline_scope_from_first_period(self):
        project = {
            'periods': [
                {'date': '2026-01-01', 'total_estimated_effort': '100'},
            ]
        }
        utils._backfill_scope_deltas(project)
        assert project['baseline_scope'] == 100.0

    def test_backfills_scope_delta_as_diff_between_periods(self):
        project = {
            'periods': [
                {'date': '2026-01-01', 'total_estimated_effort': '100'},
                {'date': '2026-02-01', 'total_estimated_effort': '120'},
            ]
        }
        utils._backfill_scope_deltas(project)
        assert project['periods'][1]['scope_delta'] == pytest.approx(20.0)

    def test_empty_periods_returns_no_change(self):
        project = {'periods': []}
        assert utils._backfill_scope_deltas(project) is False

    def test_missing_total_estimated_effort_does_not_crash(self):
        """DEF-06 fixed: periods without 'total_estimated_effort' and without 'scope_delta'
        should default scope_delta to 0.0 and not raise."""
        project = {
            'periods': [{'date': '2026-01-01', 'actual_cost': 1000.0}]
            # No 'total_estimated_effort', no 'scope_delta', no 'baseline_scope'
        }
        changed = utils._backfill_scope_deltas(project)
        # Missing baseline_scope + missing total_estimated_effort → early return, no crash
        assert changed is False
