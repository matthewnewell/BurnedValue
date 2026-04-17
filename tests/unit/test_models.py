"""
Unit tests for data model entities.

Stubs — to be implemented as SQLAlchemy models are built in Phase 1.
See docs/DATA_MODEL.md for entity definitions.
"""
import pytest


class TestFeaturePercentComplete:
    """Feature % complete = done story points / total story points."""

    @pytest.mark.skip(reason="Phase 1 — Feature model not yet implemented")
    def test_feature_with_no_stories_is_zero_percent(self):
        pass

    @pytest.mark.skip(reason="Phase 1 — Feature model not yet implemented")
    def test_feature_with_all_stories_done_is_100_percent(self):
        pass

    @pytest.mark.skip(reason="Phase 1 — Feature model not yet implemented")
    def test_feature_percent_complete_partial(self):
        """3 of 10 story points done → 30%."""
        pass

    @pytest.mark.skip(reason="Phase 1 — Feature model not yet implemented")
    def test_earned_feature_points(self):
        """earned_fp = feature_points × pct_complete."""
        pass


class TestEpicRollup:
    """Epic EV = sum of feature earned_fp."""

    @pytest.mark.skip(reason="Phase 1 — Epic model not yet implemented")
    def test_epic_percent_complete_rollup(self):
        pass

    @pytest.mark.skip(reason="Phase 1 — Epic model not yet implemented")
    def test_epic_with_no_features_is_zero(self):
        pass


class TestStoryStatusTransitions:
    """Story state machine: New → Active → Resolved → Done."""

    @pytest.mark.skip(reason="Phase 1 — Story model not yet implemented")
    def test_new_story_earns_no_ev(self):
        pass

    @pytest.mark.skip(reason="Phase 1 — Story model not yet implemented")
    def test_done_story_earns_full_story_points(self):
        pass

    @pytest.mark.skip(reason="Phase 1 — Story model not yet implemented")
    def test_active_story_earns_no_ev(self):
        """Partial completion within a story does not earn partial EV."""
        pass

    @pytest.mark.skip(reason="Phase 1 — Story model not yet implemented")
    def test_blocked_flag_does_not_change_ev(self):
        """Blocked is an attribute, not a status. EV is unchanged by blocked flag."""
        pass


class TestIterationCostRollup:
    """Iteration planned and actual cost from discipline entries."""

    @pytest.mark.skip(reason="Phase 2 — Iteration/DisciplineActual not yet implemented")
    def test_planned_cost_from_staffing_profile(self):
        """planned_cost = sum(discipline.planned_hours × avg_rate)."""
        pass

    @pytest.mark.skip(reason="Phase 2 — Iteration/DisciplineActual not yet implemented")
    def test_actual_cost_from_discipline_actuals(self):
        """actual_cost = sum(DisciplineActual.actual_dollars)."""
        pass

    @pytest.mark.skip(reason="Phase 2 — Iteration/DisciplineActual not yet implemented")
    def test_points_completed_from_done_stories(self):
        """points_completed = sum(story.story_points where status=done)."""
        pass


class TestCapacityCheck:
    """Velocity vs. scope feasibility checks."""

    @pytest.mark.skip(reason="Phase 1 — velocity model not yet implemented")
    def test_feature_fits_in_target_iterations(self):
        """feature_points / velocity <= target_duration → no risk flag."""
        pass

    @pytest.mark.skip(reason="Phase 1 — velocity model not yet implemented")
    def test_feature_exceeds_capacity_raises_flag(self):
        """feature_points / velocity > target_duration → risk flag."""
        pass
