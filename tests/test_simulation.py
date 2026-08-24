"""
Tests for simulation engine behavior.

Simulation tests now create their own SimulationRun and deterministic
business world so intervention effects are isolated to one run.
"""

from app.scripts.seed_demo_data import seed_business_world
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
from app.simulation.run_store import create_simulation_run
from app.simulation.state import SimulationState


def create_seeded_run(
    db_session,
    random_seed: int = 42,
):
    """
    Create one simulation run and seed its deterministic business world.
    """

    simulation_run = create_simulation_run(
        db_session,
        random_seed=random_seed,
    )

    seed_business_world(
        db_session,
        simulation_run_id=simulation_run.id,
    )

    return simulation_run


def test_simulation_starts_at_day_zero() -> None:
    """
    A new in-memory simulation state begins with no elapsed time
    or spending.
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


def test_intervention_does_not_finish_too_early(
    db_session,
) -> None:
    """
    An intervention should remain active until its evaluation day.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    state = SimulationState(
        random_seed=42,
    )

    activate_intervention(
        state,
        GUIDED_INTEGRATION_HELP,
    )

    advance_days(
        db_session,
        simulation_run.id,
        state,
        3,
    )

    assert state.current_day == 3

    assert (
        GUIDED_INTEGRATION_HELP
        in state.active_interventions
    )


def test_guided_integration_help_improves_outcomes(
    db_session,
) -> None:
    """
    Guided integration help should improve onboarding and conversion
    for one deterministic simulation run.
    """

    simulation_run = create_seeded_run(
        db_session,
        random_seed=42,
    )

    state = SimulationState(
        random_seed=42,
    )

    before_funnel = get_onboarding_funnel(
        db_session,
        simulation_run.id,
    )

    before_conversion = get_conversion_rate(
        db_session,
        simulation_run.id,
    )

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

    advance_days(
        db_session,
        simulation_run.id,
        state,
        7,
    )

    after_funnel = get_onboarding_funnel(
        db_session,
        simulation_run.id,
    )

    after_conversion = get_conversion_rate(
        db_session,
        simulation_run.id,
    )

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


def test_intervention_does_not_modify_another_run(
    db_session,
) -> None:
    """
    An intervention applied to one run must not modify another run.
    """

    first_run = create_seeded_run(
        db_session,
        random_seed=42,
    )

    second_run = create_seeded_run(
        db_session,
        random_seed=42,
    )

    first_state = SimulationState(
        random_seed=42,
    )

    first_before = get_conversion_rate(
        db_session,
        first_run.id,
    )

    second_before = get_conversion_rate(
        db_session,
        second_run.id,
    )

    assert first_before == 30.0
    assert second_before == 30.0

    activate_intervention(
        first_state,
        GUIDED_INTEGRATION_HELP,
    )

    advance_days(
        db_session,
        first_run.id,
        first_state,
        7,
    )

    first_after = get_conversion_rate(
        db_session,
        first_run.id,
    )

    second_after = get_conversion_rate(
        db_session,
        second_run.id,
    )

    assert first_after >= first_before

    # The second simulation world must remain untouched.
    assert second_after == second_before
    assert second_after == 30.0


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