"""
Unit tests for EVM calculation engine.

These tests are the authoritative verification of EVM math.
All formulas are defined in docs/EVM_THEORY.md.

Run: cd /home/matthew/BurnedValue && .venv/bin/pytest tests/unit/test_ev_math.py -v
"""
import pytest
from models import CalculationEngine


class TestEarnedValue:

    def test_ev_is_percent_complete_times_bac(self, simple_project, single_period):
        """EV = (points_completed / baseline_scope) × BAC"""
        metrics = CalculationEngine.compute_metrics(simple_project, single_period)
        # 50 of 100 points done = 50% × $100k BAC = $50k EV
        assert metrics['ev'] == pytest.approx(50000.0)

    def test_ev_is_zero_with_no_periods(self, simple_project):
        """No periods → no work done → EV = 0."""
        metrics = CalculationEngine.compute_metrics(simple_project, [])
        assert metrics['ev'] == 0

    def test_ev_accounts_for_scope_creep(self, simple_project, two_periods):
        """Scope grew by 20 points in period 2 (100 → 120 total).
        45 points done / 120 total = 37.5% complete × $100k = $37,500 EV.
        Note: engine returns percent_complete as 0–100, not 0–1."""
        metrics = CalculationEngine.compute_metrics(simple_project, two_periods)
        assert metrics['percent_complete'] == pytest.approx(37.5, rel=1e-3)
        assert metrics['ev'] == pytest.approx(37500.0, rel=1e-3)

    def test_percent_complete_at_100_when_all_done(self, simple_project):
        """All scope completed → 100% → EV = BAC.
        Note: engine returns percent_complete as 0–100, not 0–1."""
        periods = [{
            'period_id': 'p1',
            'date': '2026-03-01',
            'actual_cost': 90000.0,
            'points_completed': 100.0,
            'scope_delta': 0.0,
        }]
        metrics = CalculationEngine.compute_metrics(simple_project, periods)
        assert metrics['percent_complete'] == pytest.approx(100.0)
        assert metrics['ev'] == pytest.approx(100000.0)


class TestActualCost:

    def test_ac_sums_across_periods(self, simple_project, two_periods):
        """AC = sum of actual_cost across all periods."""
        metrics = CalculationEngine.compute_metrics(simple_project, two_periods)
        assert metrics['ac'] == pytest.approx(45000.0)  # 20k + 25k

    def test_ac_is_zero_with_no_periods(self, simple_project):
        metrics = CalculationEngine.compute_metrics(simple_project, [])
        assert metrics['ac'] == 0


class TestCPI:

    def test_cpi_over_budget(self, simple_project, single_period):
        """50 pts done, $45k spent → EV $50k / AC $45k = CPI 1.11 (under budget)."""
        metrics = CalculationEngine.compute_metrics(simple_project, single_period)
        assert metrics['cpi'] == pytest.approx(50000 / 45000, rel=1e-3)

    def test_cpi_exactly_one_when_on_budget(self, simple_project):
        """EV = AC → CPI = 1.0."""
        periods = [{
            'period_id': 'p1',
            'date': '2026-02-01',
            'actual_cost': 50000.0,
            'points_completed': 50.0,
            'scope_delta': 0.0,
        }]
        metrics = CalculationEngine.compute_metrics(simple_project, periods)
        assert metrics['cpi'] == pytest.approx(1.0)

    def test_cpi_below_one_when_over_budget(self, simple_project):
        """Spent more than earned → CPI < 1.0.
        Note: engine rounds CPI to 2 decimal places."""
        periods = [{
            'period_id': 'p1',
            'date': '2026-02-01',
            'actual_cost': 60000.0,
            'points_completed': 50.0,
            'scope_delta': 0.0,
        }]
        metrics = CalculationEngine.compute_metrics(simple_project, periods)
        assert metrics['cpi'] < 1.0
        assert metrics['cpi'] == pytest.approx(50000 / 60000, abs=0.01)

    def test_cpi_is_zero_with_no_periods(self, simple_project):
        metrics = CalculationEngine.compute_metrics(simple_project, [])
        assert metrics['cpi'] == 0


class TestEAC:

    def test_eac_equals_bac_divided_by_cpi(self, simple_project, single_period):
        """EAC = BAC / CPI."""
        metrics = CalculationEngine.compute_metrics(simple_project, single_period)
        expected_eac = simple_project['bac'] / metrics['cpi']
        assert metrics['eac'] == pytest.approx(expected_eac, rel=1e-3)

    def test_eac_equals_bac_when_cpi_is_one(self, simple_project):
        """On-budget project forecasts to exactly BAC."""
        periods = [{
            'period_id': 'p1',
            'date': '2026-02-01',
            'actual_cost': 50000.0,
            'points_completed': 50.0,
            'scope_delta': 0.0,
        }]
        metrics = CalculationEngine.compute_metrics(simple_project, periods)
        assert metrics['eac'] == pytest.approx(simple_project['bac'], rel=1e-3)

    def test_eac_exceeds_bac_when_over_budget(self, simple_project):
        """Over-budget project forecasts to exceed BAC."""
        periods = [{
            'period_id': 'p1',
            'date': '2026-02-01',
            'actual_cost': 60000.0,
            'points_completed': 50.0,
            'scope_delta': 0.0,
        }]
        metrics = CalculationEngine.compute_metrics(simple_project, periods)
        assert metrics['eac'] > simple_project['bac']


class TestScopeTracking:

    def test_scope_delta_increases_total_scope(self, simple_project, two_periods):
        """Scope delta of +20 → total scope = 120."""
        metrics = CalculationEngine.compute_metrics(simple_project, two_periods)
        assert metrics['total_scope'] == pytest.approx(120.0)

    def test_scope_coverage_ratio_decreases_with_creep(self, simple_project, two_periods):
        """Baseline 100, current 120 → coverage = 100/120 = 83.3%."""
        metrics = CalculationEngine.compute_metrics(simple_project, two_periods)
        assert metrics['scope_coverage_ratio'] == pytest.approx(83.3, rel=1e-2)

    def test_scope_coverage_ratio_is_100_without_creep(self, simple_project, single_period):
        """No scope change → coverage ratio = 100%."""
        metrics = CalculationEngine.compute_metrics(simple_project, single_period)
        assert metrics['scope_coverage_ratio'] == pytest.approx(100.0)


class TestVelocity:

    def test_avg_velocity_is_points_per_period(self, simple_project, two_periods):
        """Two periods: 25 + 20 = 45 points, avg = 22.5."""
        metrics = CalculationEngine.compute_metrics(simple_project, two_periods)
        assert metrics['avg_velocity'] == pytest.approx(22.5)

    def test_avg_velocity_zero_with_no_periods(self, simple_project):
        metrics = CalculationEngine.compute_metrics(simple_project, [])
        assert metrics['avg_velocity'] == 0


class TestEdgeCases:

    def test_zero_bac_does_not_crash(self):
        """Degenerate project with BAC=0 should not raise."""
        project = {
            'id': 'zero-bac',
            'bac': 0.0,
            'baseline_scope': 100.0,
            'start_date': '2026-01-01',
            'end_date': '2026-06-30',
            'interval_unit': 'weeks',
            'interval_size': 2,
        }
        periods = [{'period_id': 'p1', 'date': '2026-01-15',
                    'actual_cost': 0.0, 'points_completed': 10.0, 'scope_delta': 0.0}]
        # Should not raise — may return 0s
        metrics = CalculationEngine.compute_metrics(project, periods)
        assert isinstance(metrics, dict)

    def test_zero_scope_does_not_divide_by_zero(self, simple_project):
        """If baseline_scope is 0, calculation should not crash."""
        project = {**simple_project, 'baseline_scope': 0.0}
        periods = [{'period_id': 'p1', 'date': '2026-01-15',
                    'actual_cost': 10000.0, 'points_completed': 0.0, 'scope_delta': 0.0}]
        metrics = CalculationEngine.compute_metrics(project, periods)
        assert isinstance(metrics, dict)

    def test_negative_scope_delta_reduces_scope(self, simple_project):
        """Scope reduction (descoping) should reduce total scope."""
        periods = [
            {'period_id': 'p1', 'date': '2026-01-15',
             'actual_cost': 20000.0, 'points_completed': 30.0, 'scope_delta': -20.0},
        ]
        metrics = CalculationEngine.compute_metrics(simple_project, periods)
        assert metrics['total_scope'] == pytest.approx(80.0)
