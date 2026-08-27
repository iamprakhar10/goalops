"""
Evaluation utilities for our autonomous operator

This module evaluates the behaviour of the autonomous operator after a 
run completes

Business goal success is only one part of evaluation. We also measure
cost, time, number of decisions, interventions used, and whether the 
operator gathered business evidence before taking an intervention
"""


from dataclasses import dataclass


from app.database.db import SessionLocal
from app.operator.session_store import (
    get_operator_sessions_for_run,
    get_operator_tool_calls_for_run,
)
from app.simulation.run_store import (
    get_simulation_run,
    get_simulation_run_intervention_history,
)


from app.operator.runner import OperatorRunState
from app.operator.schemas import OperatorAction
from app.operator.tool_runner import ToolOperatorRunState


from app.mcp.tools import (
    evaluate_business_goal,
)





@dataclass(frozen=True)
class OperatorRunEvaluation:
    """
    Summary of one autonomous Operator run

    goal_status:
        Final objective state of the business goal

    final_metric:
        Final value of goal metric

    target_value:
        Required metric value

    total_spend:
        Intervention money spent during the run

    days_used:
        Number of simulated days consumed

    decisions_made:
        Number of LLM decisions executed

    interventions_launched:
        Names of interventions selected by the agent

    inspected_business:
        Whether the agent called inspect_business at least once

    inspected_before_first_intervention:
        Whether business evidence was inspected before the first
        intervention was launched.

    """

    goal_status: str
    final_metric: float
    target_value: float

    total_spend: float
    days_used: int

    decisions_made: int

    interventions_launched: list[str]

    inspected_business: bool
    inspected_before_first_intervention: bool

    #termination_reason: str







def evaluate_operator_run(
        run_state: OperatorRunState,
) -> OperatorRunEvaluation:
    """
    Evaluate one completed aotonomous operator run

    This function won't ask the LLM whether it performed well.

    Instead, it calculates evaluation data directly from the recorded
    run statr and final goal status
    """

    if run_state.final_goal_status is None:
        raise ValueError(
            "Cannot eveluate operator run without final goal status"
        )

    # ---------------------------------------------------------
    # FIND WHICH INTERVENTIONS WERE LAUNCHED
    # ---------------------------------------------------------

    interventions_launched = [
        decision.intervention_name
        for decision in run_state.decisions
        if (
            decision.action
            == OperatorAction.LAUNCH_INTERVENTION
            and decision.intervention_name
        )
    ]

    # ---------------------------------------------------------
    # DID THE AGENT INSPECT THE BUSINESS?
    # ---------------------------------------------------------

    inspected_business = any(
        decision.action
        == OperatorAction.INSPECT_BUSINESS
        for decision in run_state.decisions
    )

    # ---------------------------------------------------------
    # DID INSPECTION HAPPEN BEFORE SPENDING MONEY?
    # ---------------------------------------------------------

    first_inspection_index: int | None = None
    first_intervention_index: int | None = None

    for index, decision in enumerate(
        run_state.decisions
    ):
        if (
            decision.action
            == OperatorAction.INSPECT_BUSINESS
            and first_inspection_index is None
        ):
            first_inspection_index = index

        if (
            decision.action
            == OperatorAction.LAUNCH_INTERVENTION
            and first_intervention_index is None
        ):
            first_intervention_index = index

    inspected_before_first_intervention = (
        first_inspection_index is not None
        and first_intervention_index is not None
        and first_inspection_index
        < first_intervention_index
    )

    goal_status = run_state.final_goal_status

    return OperatorRunEvaluation(
        goal_status=goal_status['status'],
        final_metric=goal_status['current_value'],
        target_value=goal_status['target_value'],
        total_spend=(
            goal_status["max_budget"]
            - goal_status["budget_remaining"]
        ),
        days_used=(
            goal_status["deadline_day"]
            - goal_status["days_remaining"]
        ),
        decisions_made=len(
            run_state.decisions
        ),
        interventions_launched=(
            interventions_launched
        ),
        inspected_business=inspected_business,
        inspected_before_first_intervention=(
            inspected_before_first_intervention
        ),
    )














#_________________________________________________________

# For tool operator
#_________________________________________________________


def evaluate_tool_operator_run(
        run_id: int,
) -> OperatorRunEvaluation:
    """
    Evaluate one COMPLETED MCP-native simulation run

    The evaluation includes operator behaviour from every operator
    session belonging to the simulation run, including resumed sessions.
    """

    db = SessionLocal()

    try:

        tool_calls = get_operator_tool_calls_for_run(
            db=db,
            simulation_run_id=run_id,
        )

        # operator_session = get_operator_sessions_for_run(
        #     db,
        #     run_id,
        # )

        intervention_history = get_simulation_run_intervention_history(
            db,
            run_id=run_id,
        )

        # -----------------------------------------------------
        # OBJECTIVE FINAL BUSINESS RESULT
        # -----------------------------------------------------
        #
        # Use the exact same deterministic goal evaluation that the MCP
        # goal_status tool uses
        # We don't infer success from the LLM or from old tool results
        final_goal_status = evaluate_business_goal(
            run_id=run_id
        )


        # -----------------------------------------------------
        # INTERVENTIONS
        # -----------------------------------------------------
        #
        # SimulationRunIntervention is the source of truth for
        # interventions that were actually launched in the business.

        interventions_launched = [
            intervention['name']
            for intervention in intervention_history
        ]

        # -----------------------------------------------------
        # BUSINESS INSPECTION
        # -----------------------------------------------------

        inspected_business = any(
            tool_call.tool_name == 'business_snapshot'
            for tool_call in tool_calls
        )

        # -----------------------------------------------------
        # INSPECTION BEFORE FIRST INTERVENTION
        # -----------------------------------------------------

        first_business_snapshot_index: int | None = None
        first_intervention_index: int | None = None

        for index, tool_call in enumerate(
            tool_calls
        ):
            if (
                first_business_snapshot_index is None
                and tool_call.tool_name
                == "business_snapshot"
            ):
                first_business_snapshot_index = index

            if (
                first_intervention_index is None
                and tool_call.tool_name
                == "run_intervention"
            ):
                first_intervention_index = index

        if first_intervention_index is None:
            inspected_before_first_intervention = (
                inspected_business
            )
        else:
            inspected_before_first_intervention = (
                first_business_snapshot_index is not None
                and first_business_snapshot_index
                < first_intervention_index
            )

        # -----------------------------------------------------
        # FULL RUN METRICS
        # -----------------------------------------------------
        decisions_made = len(
            tool_calls
        )

        total_spend = (
            final_goal_status['max_budget']
            - final_goal_status['budget_remaining']
        )

        days_used = (
            final_goal_status["deadline_day"]
            - final_goal_status["days_remaining"]
        )

        return OperatorRunEvaluation(
            goal_status=final_goal_status["status"],
            final_metric=final_goal_status[
                "current_value"
            ],
            target_value=final_goal_status[
                "target_value"
            ],
            total_spend=total_spend,
            days_used=days_used,
            decisions_made=decisions_made,
            interventions_launched=(
                interventions_launched
            ),
            inspected_business=(
                inspected_business
            ),
            inspected_before_first_intervention=(
                inspected_before_first_intervention
            ),
        )

    finally:
        db.close()