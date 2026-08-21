"""
Tests for autonomous operator run evaluation.

These tests verify that GoalOps measures agent behavior correctly
without depending on Groq or making external API calls.
"""

from app.operator.evaluation import evaluate_operator_run
from app.operator.runner import OperatorRunState
from app.operator.schemas import (
    OperatorAction,
    OperatorDecision,
)


def make_decision(
    action: OperatorAction,
    intervention_name: str = "",
    days: int = 0,
) -> OperatorDecision:
    """
    Create a simple operator decision for evaluation tests.
    """

    return OperatorDecision(
        action=action,
        reasoning_summary="test decision",
        intervention_name=intervention_name,
        days=days,
    )


def test_evaluation_records_success_and_cost() -> None:
    """
    A successful run should correctly calculate cost and time used.
    """

    run_state = OperatorRunState(
        iteration=4,
        decisions=[
            make_decision(
                OperatorAction.INSPECT_BUSINESS,
            ),
            make_decision(
                OperatorAction.INSPECT_INTERVENTIONS,
            ),
            make_decision(
                OperatorAction.LAUNCH_INTERVENTION,
                intervention_name="guided_integration_help",
            ),
            make_decision(
                OperatorAction.ADVANCE_TIME,
                days=7,
            ),
        ],
        final_goal_status={
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

    evaluation = evaluate_operator_run(
        run_state
    )

    assert evaluation.goal_status == "achieved"
    assert evaluation.final_metric == 45.0

    assert evaluation.total_spend == 1200.0
    assert evaluation.days_used == 7

    assert evaluation.decisions_made == 4

    assert evaluation.interventions_launched == [
        "guided_integration_help"
    ]

    assert evaluation.inspected_business is True

    assert (
        evaluation.inspected_before_first_intervention
        is True
    )





def test_evaluation_detects_action_without_business_inspection() -> None:
    """
    Evaluation should detect when the agent spends money before
    inspecting business evidence.
    """

    run_state = OperatorRunState(
        iteration=2,
        decisions=[
            make_decision(
                OperatorAction.INSPECT_INTERVENTIONS,
            ),
            make_decision(
                OperatorAction.LAUNCH_INTERVENTION,
                intervention_name="onboarding_email",
            ),
        ],
        final_goal_status={
            "metric_name": "trial_to_paid_conversion",
            "target_value": 40.0,
            "current_value": 35.0,
            "status": "in_progress",
            "max_budget": 2000.0,
            "budget_remaining": 1700.0,
            "deadline_day": 30,
            "days_remaining": 30,
        },
    )

    evaluation = evaluate_operator_run(
        run_state
    )

    assert evaluation.inspected_business is False

    assert (
        evaluation.inspected_before_first_intervention
        is False
    )