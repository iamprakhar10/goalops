"""
Tests for full-run autonomous operator evaluation.

These tests verify that evaluation reads persisted operator history
from the database rather than relying on one in-memory
ToolOperatorRunState.

A simulation run may contain multiple operator sessions when the run
is stopped and later resumed.
"""

from app.operator.evaluation import (
    evaluate_tool_operator_run,
)
from app.operator.session_store import (
    complete_operator_session,
    create_operator_session,
    save_operator_tool_call,
)
from app.simulation.run_store import (
    create_simulation_run,
    save_simulation_state,
)
from app.simulation.state import (
    SimulationState,
)
from app.simulation.engine import (
    activate_intervention,
)


def test_tool_operator_evaluation(
    db_session,
) -> None:
    """
    Evaluation should use persisted history from the complete
    simulation run.
    """

    # ---------------------------------------------------------
    # CREATE PERSISTENT SIMULATION RUN
    # ---------------------------------------------------------

    simulation_run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    run_id = simulation_run.id

    # ---------------------------------------------------------
    # CREATE BUSINESS STATE
    # ---------------------------------------------------------
    #
    # We persist one launched intervention so that
    # get_simulation_run_intervention_history() has real data.
    #

    state = SimulationState(
        random_seed=42,
    )

    activate_intervention(
        state,
        "guided_integration_help",
    )

    save_simulation_state(
        db_session,
        run_id,
        state,
    )

    db_session.commit()

    # ---------------------------------------------------------
    # FIRST OPERATOR SESSION
    # ---------------------------------------------------------

    first_session = create_operator_session(
        db_session,
        simulation_run_id=run_id,
    )

    save_operator_tool_call(
        db_session,
        operator_session_id=first_session.id,
        sequence_number=1,
        tool_name="business_snapshot",
        arguments={
            "run_id": run_id,
        },
        result={
            "conversion_rate": 30.0,
        },
    )

    save_operator_tool_call(
        db_session,
        operator_session_id=first_session.id,
        sequence_number=2,
        tool_name="available_interventions",
        arguments={},
        result={
            "result": [
                {
                    "name": "guided_integration_help",
                }
            ],
        },
    )

    save_operator_tool_call(
        db_session,
        operator_session_id=first_session.id,
        sequence_number=3,
        tool_name="run_intervention",
        arguments={
            "run_id": run_id,
            "intervention_name": (
                "guided_integration_help"
            ),
        },
        result={
            "run_id": run_id,
            "name": "guided_integration_help",
            "started_day": 0,
            "evaluation_day": 7,
            "total_spend": 1200.0,
        },
    )

    complete_operator_session(
        db_session,
        operator_session_id=first_session.id,
        termination_reason="max_tool_rounds",
    )

    # ---------------------------------------------------------
    # SECOND OPERATOR SESSION
    # ---------------------------------------------------------
    #
    # This represents a later resume of the same simulation run.
    #

    second_session = create_operator_session(
        db_session,
        simulation_run_id=run_id,
    )

    save_operator_tool_call(
        db_session,
        operator_session_id=second_session.id,
        sequence_number=1,
        tool_name="business_snapshot",
        arguments={
            "run_id": run_id,
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
            "run_id": run_id,
        },
        result={
            "run_id": run_id,
            "metric_name": "trial_to_paid_conversion",
            "target_value": 40.0,
            "current_value": 45.0,
            "status": "achieved",
            "max_budget": 2000.0,
            "budget_remaining": 800.0,
            "deadline_day": 30,
            "days_remaining": 23,
        },
    )

    complete_operator_session(
        db_session,
        operator_session_id=second_session.id,
        termination_reason="goal_achieved",
    )

    db_session.commit()

    # ---------------------------------------------------------
    # EVALUATE COMPLETE RUN
    # ---------------------------------------------------------

    evaluation = evaluate_tool_operator_run(
        run_id=run_id,
    )

    # Five persisted tool calls across both sessions:
    #
    # Session 1:
    # 1. business_snapshot
    # 2. available_interventions
    # 3. run_intervention
    #
    # Session 2:
    # 4. business_snapshot
    # 5. goal_status
    assert evaluation.decisions_made == 5

    assert evaluation.inspected_business is True

    assert (
        evaluation.inspected_before_first_intervention
        is True
    )

    assert evaluation.interventions_launched == [
        "guided_integration_help",
    ]

    assert evaluation.operator_session_count == 2

    assert evaluation.resume_count == 1

    assert evaluation.termination_history == [
        "max_tool_rounds",
        "goal_achieved",
    ]