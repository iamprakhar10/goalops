"""
Tests for the GoalOps MCP tool implementation layer.

These tests verify that MCP-facing functions expose controlled access to
business analytics, interventions, time advancement, and goal evaluation
without requiring direct database access from the future autonomous agent.
"""

from app.mcp.tools import (
    business_goal,
    evaluate_business_goal,
    get_business_snapshot,
    list_available_interventions,
    simulation_state,
)
from app.simulation.interventions import (
    GUIDED_INTEGRATION_HELP,
)

def reset_simulation_state() -> None:
    """
    Reset the in-memory MCP simulation state between tests.
    """

    simulation_state.current_day = 0
    simulation_state.active_interventions.clear()
    simulation_state.total_spend = 0.0
    simulation_state.random_seed = 42


def test_business_snapshot_exposes_baseline_metrics() -> None:
    """
    The MCP analytics boundary should expose the known benchmark baseline.
    """
    reset_simulation_state()
    snapshot = get_business_snapshot()

    assert snapshot["current_day"] == 0
    assert snapshot["conversion_rate"] == 30.0

    assert snapshot["onboarding_funnel"][
        "started_trial"
    ] == 20


def test_intervention_catalog_is_exposed() -> None:
    """
    The operator should receive a bounded list of allowed actions.
    """
    reset_simulation_state()
    interventions = list_available_interventions()

    names = {
        intervention["name"]
        for intervention in interventions
    }

    assert GUIDED_INTEGRATION_HELP in names


def test_goal_is_exposed_through_tool_boundary() -> None:
    """
    Goal evaluation should be available without exposing evaluator internals.
    """
    reset_simulation_state()
    evaluation = evaluate_business_goal()

    assert (
        evaluation["metric_name"]
        == business_goal.metric_name
    )

    assert evaluation["status"] == "in_progress"