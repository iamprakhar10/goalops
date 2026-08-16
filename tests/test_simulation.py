"""
Tests for the fake SaaS business simulation engine.

These tests verify that simulated time and interventions change business
data according to predefined rules.

The tests also verify that the autonomous operator will not need to
directly manipulate customer outcomes.
"""

from app.database.db import SessionLocal
from app.services.analytics import (
    get_conversion_rate,
    get_onboarding_funnel,
)
from app.simulation.engine import (
    GUIDED_INTEGRATION_HELP,
    activate_intervention,
    advance_days,
)
from app.simulation.state import SimulationState


def test_simulation_starts_at_day_zero() -> None:
    """
    A new simulation run begins at simulated day zero.
    """

    state = SimulationState()

    assert state.current_day == 0
    assert state.active_interventions == set()


def test_intervention_can_be_activated() -> None:
    """
    The guided integration intervention can be enabled.
    """

    state = SimulationState()

    activate_intervention(
        state,
        GUIDED_INTEGRATION_HELP,
    )

    assert (
        GUIDED_INTEGRATION_HELP
        in state.active_interventions
    )


def test_guided_integration_help_improves_outcomes() -> None:
    """
    Guided integration help should cause eligible stalled companies
    to progress when simulated time advances.

    This test assumes the deterministic demo seed is loaded first.
    """

    db = SessionLocal()

    try:
        state = SimulationState()

        before_funnel = get_onboarding_funnel(db)
        before_conversion = get_conversion_rate(db)

        assert before_funnel["completed_onboarding"] == 6
        assert before_funnel["converted_to_paid"] == 6
        assert before_conversion == 30.0

        activate_intervention(
            state,
            GUIDED_INTEGRATION_HELP,
        )

        advance_days(
            db,
            state,
            7,
        )

        after_funnel = get_onboarding_funnel(db)
        after_conversion = get_conversion_rate(db)

        assert state.current_day == 7

        assert after_funnel["completed_onboarding"] == 10
        assert after_funnel["converted_to_paid"] == 8

        assert after_conversion == 40.0

    finally:
        db.rollback()
        db.close()