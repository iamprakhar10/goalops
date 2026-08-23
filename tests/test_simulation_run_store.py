"""
Tests for persistent simulation run storage.

These tests verify that simulation runs can be created in PostgreSQL
and reconstructed as SimulationState objects.
"""

from app.simulation.run_store import (
    create_simulation_run,
    load_simulation_state,
    save_simulation_state
)
from app.simulation.interventions import ActiveIntervention


def test_create_simulation_run(
    db_session,
) -> None:
    """
    A newly created run should start with clean simulation state.
    """

    run = create_simulation_run(
        db_session,
        random_seed=123,
    )

    assert run.id is not None
    assert run.current_day == 0
    assert run.total_spend == 0.0
    assert run.random_seed == 123
    assert run.status == "active"


def test_load_simulation_state(
    db_session,
) -> None:
    """
    Stored run data should reconstruct a SimulationState.
    """

    run = create_simulation_run(
        db_session,
        random_seed=456,
    )

    state = load_simulation_state(
        db_session,
        run.id,
    )

    assert state.current_day == 0
    assert state.total_spend == 0.0
    assert state.random_seed == 456
    assert state.active_interventions == {}





def test_save_and_reload_simulation_state(
    db_session,
) -> None:
    """
    Changes made to SimulationState should survive reconstruction from
    the database.
    """

    run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    state = load_simulation_state(
        db_session,
        run.id,
    )

    state.current_day = 7
    state.total_spend = 1200.0

    save_simulation_state(
        db_session,
        run.id,
        state,
    )

    reloaded_state = load_simulation_state(
        db_session,
        run.id,
    )

    assert reloaded_state.current_day == 7
    assert reloaded_state.total_spend == 1200.0
    assert reloaded_state.random_seed == 42





def test_active_intervention_survives_reload(
    db_session,
) -> None:
    """
    Active interventions should survive conversion between Python state
    and persistent database state.
    """

    run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    state = load_simulation_state(
        db_session,
        run.id,
    )

    state.active_interventions[
        "onboarding_email"
    ] = ActiveIntervention(
        name="onboarding_email",
        started_day=0,
        evaluation_day=7,
    )

    save_simulation_state(
        db_session,
        run.id,
        state,
    )

    reloaded_state = load_simulation_state(
        db_session,
        run.id,
    )

    intervention = (
        reloaded_state
        .active_interventions[
            "onboarding_email"
        ]
    )

    assert intervention.started_day == 0
    assert intervention.evaluation_day == 7