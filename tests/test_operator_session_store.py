"""
Tests for persistent autonomous operator session history.

These tests verify that operator sessions and MCP tool calls can be
stored and reconstructed across multiple sessions of the same
simulation run.
"""

from app.operator.session_store import (
    complete_operator_session,
    create_operator_session,
    get_operator_sessions_for_run,
    get_operator_tool_calls_for_run,
    save_operator_tool_call,
)
from app.simulation.run_store import (
    create_simulation_run,
)


def test_create_operator_session(
    db_session,
) -> None:
    """
    A new operator session should belong to the specified
    simulation run.
    """

    simulation_run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    operator_session = create_operator_session(
        db_session,
        simulation_run.id,
    )

    assert operator_session.id is not None

    assert (
        operator_session.simulation_run_id
        == simulation_run.id
    )

    assert (
        operator_session.termination_reason
        is None
    )

    assert operator_session.completed_at is None


def test_save_operator_tool_call(
    db_session,
) -> None:
    """
    Tool calls should be persisted with their arguments,
    results, and execution order.
    """

    simulation_run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    operator_session = create_operator_session(
        db_session,
        simulation_run.id,
    )

    tool_call = save_operator_tool_call(
        db_session,
        operator_session_id=operator_session.id,
        sequence_number=1,
        tool_name="business_snapshot",
        arguments={
            "run_id": simulation_run.id,
        },
        result={
            "conversion_rate": 30.0,
        },
    )

    assert tool_call.id is not None

    assert (
        tool_call.operator_session_id
        == operator_session.id
    )

    assert tool_call.sequence_number == 1

    assert (
        tool_call.tool_name
        == "business_snapshot"
    )

    assert tool_call.arguments == {
        "run_id": simulation_run.id,
    }

    assert tool_call.result == {
        "conversion_rate": 30.0,
    }


def test_complete_operator_session(
    db_session,
) -> None:
    """
    Completing a session should record why it stopped
    and when it completed.
    """

    simulation_run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    operator_session = create_operator_session(
        db_session,
        simulation_run.id,
    )

    completed_session = complete_operator_session(
        db_session,
        operator_session_id=operator_session.id,
        termination_reason="max_tool_rounds",
    )

    assert (
        completed_session.termination_reason
        == "max_tool_rounds"
    )

    assert completed_session.completed_at is not None


def test_invalid_termination_reason_is_rejected(
    db_session,
) -> None:
    """
    Unknown termination reasons should not be persisted.
    """

    simulation_run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    operator_session = create_operator_session(
        db_session,
        simulation_run.id,
    )

    try:
        complete_operator_session(
            db_session,
            operator_session_id=operator_session.id,
            termination_reason="something_random",
        )

        assert False

    except ValueError:
        pass


def test_operator_sessions_are_scoped_to_run(
    db_session,
) -> None:
    """
    Session history from one simulation run should not leak
    into another simulation run.
    """

    run_one = create_simulation_run(
        db_session,
        random_seed=1,
    )

    run_two = create_simulation_run(
        db_session,
        random_seed=2,
    )

    session_one = create_operator_session(
        db_session,
        run_one.id,
    )

    create_operator_session(
        db_session,
        run_two.id,
    )

    sessions = get_operator_sessions_for_run(
        db_session,
        run_one.id,
    )

    assert len(sessions) == 1

    assert (
        sessions[0].id
        == session_one.id
    )


def test_tool_calls_are_reconstructed_across_resumed_sessions(
    db_session,
) -> None:
    """
    Tool-call history should include calls from every operator
    session belonging to the same simulation run.
    """

    simulation_run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    first_session = create_operator_session(
        db_session,
        simulation_run.id,
    )

    save_operator_tool_call(
        db_session,
        operator_session_id=first_session.id,
        sequence_number=1,
        tool_name="business_snapshot",
        arguments={
            "run_id": simulation_run.id,
        },
        result={
            "conversion_rate": 30.0,
        },
    )

    save_operator_tool_call(
        db_session,
        operator_session_id=first_session.id,
        sequence_number=2,
        tool_name="run_intervention",
        arguments={
            "run_id": simulation_run.id,
            "intervention_name": (
                "guided_integration_help"
            ),
        },
        result={
            "started_day": 0,
        },
    )

    complete_operator_session(
        db_session,
        operator_session_id=first_session.id,
        termination_reason="max_tool_rounds",
    )

    # Represents a later call to:
    #
    # run_tool_operator(run_id=...)
    second_session = create_operator_session(
        db_session,
        simulation_run.id,
    )

    save_operator_tool_call(
        db_session,
        operator_session_id=second_session.id,
        sequence_number=1,
        tool_name="business_snapshot",
        arguments={
            "run_id": simulation_run.id,
        },
        result={
            "conversion_rate": 35.0,
        },
    )

    save_operator_tool_call(
        db_session,
        operator_session_id=second_session.id,
        sequence_number=2,
        tool_name="goal_status",
        arguments={
            "run_id": simulation_run.id,
        },
        result={
            "status": "achieved",
        },
    )

    complete_operator_session(
        db_session,
        operator_session_id=second_session.id,
        termination_reason="goal_achieved",
    )

    sessions = get_operator_sessions_for_run(
        db_session,
        simulation_run.id,
    )

    assert len(sessions) == 2

    assert (
        sessions[0].termination_reason
        == "max_tool_rounds"
    )

    assert (
        sessions[1].termination_reason
        == "goal_achieved"
    )

    tool_calls = get_operator_tool_calls_for_run(
        db_session,
        simulation_run.id,
    )

    assert len(tool_calls) == 4

    assert [
        tool_call.tool_name
        for tool_call in tool_calls
    ] == [
        "business_snapshot",
        "run_intervention",
        "business_snapshot",
        "goal_status",
    ]

    assert (
        tool_calls[0].operator_session_id
        == first_session.id
    )

    assert (
        tool_calls[2].operator_session_id
        == second_session.id
    )