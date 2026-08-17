"""
Tests for the SaaS business simulation engine.

These tests verify intervention activation, simulated duration,
intervention costs, probabilistic customer outcomes, and transaction
behavior.
"""

from app.database.db import SessionLocal
from app.services.analytics import (
    get_conversion_rate,
    get_onboarding_funnel,
)
from app.simulation.engine import (
    activate_intervention,
    advance_days,
)
from app.simulation.interventions import (
    GUIDED_INTEGRATION_HELP,
)
from app.simulation.state import SimulationState


def test_simulation_starts_at_day_zero() -> None:
    """
    A new simulation begins with no elapsed time or spending.
    """

    state = SimulationState()

    assert state.current_day == 0
    assert state.active_interventions == {}
    assert state.total_spend == 0.0


def test_intervention_activation_records_cost_and_duration() -> None:
    """
    Launching guided integration help should record its duration
    and simulated financial cost.
    """

    state = SimulationState()

    intervention = activate_intervention(
        state,
        GUIDED_INTEGRATION_HELP,
    )

    assert intervention.started_day == 0
    assert intervention.evaluation_day == 7

    assert state.total_spend == 1200.0

    assert (
        GUIDED_INTEGRATION_HELP
        in state.active_interventions
    )


def test_intervention_does_not_finish_too_early() -> None:
    """
    An intervention should remain active until its evaluation day.
    """

    db = SessionLocal()

    try:
        state = SimulationState()

        activate_intervention(
            state,
            GUIDED_INTEGRATION_HELP,
        )

        advance_days(
            db,
            state,
            3,
        )

        assert state.current_day == 3

        assert (
            GUIDED_INTEGRATION_HELP
            in state.active_interventions
        )

    finally:
        db.rollback()
        db.close()


def test_guided_integration_help_improves_outcomes() -> None:
    """
    Guided integration help should improve onboarding and conversion
    for the deterministic benchmark seed.

    Database changes are rolled back after the test.
    """

    db = SessionLocal()

    try:
        state = SimulationState(
            random_seed=42,
        )

        before_funnel = get_onboarding_funnel(db)
        before_conversion = get_conversion_rate(db)

        assert (
            before_funnel["completed_onboarding"]
            == 6
        )

        assert (
            before_funnel["converted_to_paid"]
            == 6
        )

        assert before_conversion == 30.0

        activate_intervention(
            state,
            GUIDED_INTEGRATION_HELP,
        )

        # Intervention takes seven simulated days.
        advance_days(
            db,
            state,
            7,
        )

        after_funnel = get_onboarding_funnel(db)
        after_conversion = get_conversion_rate(db)

        assert state.current_day == 7

        assert (
            GUIDED_INTEGRATION_HELP
            not in state.active_interventions
        )

        assert (
            after_funnel["completed_onboarding"]
            > before_funnel["completed_onboarding"]
        )

        assert (
            after_funnel["converted_to_paid"]
            >= before_funnel["converted_to_paid"]
        )

        assert (
            after_conversion
            >= before_conversion
        )

    finally:
        db.rollback()
        db.close()


def test_unknown_intervention_is_rejected() -> None:
    """
    The simulator must reject actions that are not part of the
    approved intervention catalog.
    """

    state = SimulationState()

    try:
        activate_intervention(
            state,
            "make_every_customer_pay",
        )

        assert False

    except ValueError:
        pass