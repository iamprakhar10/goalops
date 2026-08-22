"""
Tests for persistent simulation run storage.

These tests verify that simulation runs can be created in PostgreSQL
and reconstructed as SimulationState objects.
"""

from app.simulation.run_store import (
    create_simulation_run,
    load_simulation_state,
)


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