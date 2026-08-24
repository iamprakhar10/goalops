"""
Tests for run-scoped business goal evaluation.

Each test creates its own SimulationRun and deterministic business
world so goal metrics are evaluated only for that run.
"""

from app.goals.evaluator import evaluate_goal
from app.goals.models import BusinessGoal
from app.scripts.seed_demo_data import seed_business_world
from app.simulation.run_store import create_simulation_run
from app.simulation.state import SimulationState


def create_seeded_run(
    db_session,
    random_seed: int = 42,
):
    """
    Create one simulation run with the deterministic baseline business.
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


def create_conversion_goal() -> BusinessGoal:
    """
    Return the first GoalOps benchmark goal.
    """

    return BusinessGoal(
        metric_name="trial_to_paid_conversion",
        target_value=40.0,
        deadline_day=30,
        max_budget=2000.0,
    )


def test_goal_starts_in_progress(
    db_session,
) -> None:
    """
    Baseline conversion is 30 percent, below the 40 percent target,
    so the goal should initially be in progress.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    state = SimulationState(
        current_day=0,
        total_spend=0.0,
        random_seed=42,
    )

    goal = create_conversion_goal()

    result = evaluate_goal(
        db_session,
        simulation_run.id,
        state,
        goal,
    )

    assert result.current_value == 30.0
    assert result.status == "in_progress"

    assert result.budget_remaining == 2000.0
    assert result.days_remaining == 30


def test_goal_fails_when_budget_is_exceeded(
    db_session,
) -> None:
    """
    The goal should fail when intervention spending exceeds the
    maximum allowed budget before the target has been achieved.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    state = SimulationState(
        current_day=5,
        total_spend=2100.0,
        random_seed=42,
    )

    goal = create_conversion_goal()

    result = evaluate_goal(
        db_session,
        simulation_run.id,
        state,
        goal,
    )

    assert result.current_value == 30.0
    assert result.status == "failed"

    assert result.budget_remaining == -100.0
    assert result.days_remaining == 25


def test_goal_fails_at_deadline_without_target(
    db_session,
) -> None:
    """
    Reaching the deadline without achieving the target should fail
    the business goal.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    state = SimulationState(
        current_day=30,
        total_spend=500.0,
        random_seed=42,
    )

    goal = create_conversion_goal()

    result = evaluate_goal(
        db_session,
        simulation_run.id,
        state,
        goal,
    )

    assert result.current_value == 30.0
    assert result.status == "failed"

    assert result.budget_remaining == 1500.0
    assert result.days_remaining == 0