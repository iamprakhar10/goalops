"""
Tests for evaluation of MCP-native autonomous operator runs.

These tests use fake recorded tool calls and make no Groq API requests.
"""

from app.operator.evaluation import (
    evaluate_tool_operator_run,
)
from app.operator.tool_runner import (
    ToolOperatorRunState,
)


def test_tool_operator_evaluation() -> None:
    """
    Evaluation should correctly measure an MCP-native successful run.
    """

    run_state = ToolOperatorRunState(
        run_id=123,

        tool_calls=[
            {
                "tool_name": "business_snapshot",
                "arguments": {
                    "run_id": 123,
                },
                "result": {},
            },
            {
                "tool_name": "available_interventions",
                "arguments": {},
                "result": {},
            },
            {
                "tool_name": "run_intervention",
                "arguments": {
                    "run_id": 123,
                    "intervention_name": (
                        "guided_integration_help"
                    ),
                },
                "result": {},
            },
            {
                "tool_name": "advance_time",
                "arguments": {
                    "run_id": 123,
                    "days": 7,
                },
                "result": {},
            },
            {
                "tool_name": "goal_status",
                "arguments": {
                    "run_id": 123,
                },
                "result": {},
            },
        ],

        final_goal_status={
            "run_id": 123,
            "metric_name": (
                "trial_to_paid_conversion"
            ),
            "target_value": 40.0,
            "current_value": 45.0,
            "status": "achieved",
            "max_budget": 2000.0,
            "budget_remaining": 800.0,
            "deadline_day": 30,
            "days_remaining": 23,
        },

        rounds=5,
    )

    evaluation = evaluate_tool_operator_run(
        run_state
    )

    assert evaluation.goal_status == "achieved"
    assert evaluation.final_metric == 45.0
    assert evaluation.target_value == 40.0

    assert evaluation.total_spend == 1200.0
    assert evaluation.days_used == 7

    assert evaluation.decisions_made == 5

    assert evaluation.interventions_launched == [
        "guided_integration_help"
    ]

    assert evaluation.inspected_business is True

    assert (
        evaluation.inspected_before_first_intervention
        is True
    )