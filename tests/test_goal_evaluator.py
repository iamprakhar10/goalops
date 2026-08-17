"""
Tests for measurable business-goal evaluation.

These tests verify that GoalOps can objectively determine whether an
autonomous operator has achieved a target, violated its budget, or
missed its simulated deadline.
"""

from app.database.db import SessionLocal
from app.goals.evaluator import evaluate_goal
from app.goals.models import (
    BusinessGoal,
    GoalStatus,
)
from app.simulation.state import SimulationState


def make_conversion_goal() -> BusinessGoal:
    """
    Return the first benchmark conversion goal.
    """

    return BusinessGoal(
        metric_name="trial_to_paid_conversion",
        target_value=40.0,
        deadline_day=30,
        max_budget=2000.0,
    )


def test_goal_starts_in_progress() -> None:
    """
    Baseline conversion is below the target, so the benchmark
    should initially be in progress.
    """

    db = SessionLocal()

    try:
        state = SimulationState()
        goal = make_conversion_goal()

        evaluation = evaluate_goal(
            db,
            state,
            goal,
        )

        assert evaluation.current_value == 30.0
        assert evaluation.status == GoalStatus.IN_PROGRESS
        assert evaluation.budget_remaining == 2000.0
        assert evaluation.days_remaining == 30

    finally:
        db.close()


def test_goal_fails_when_budget_is_exceeded() -> None:
    """
    Spending above the allowed budget should immediately fail the goal.
    """

    db = SessionLocal()

    try:
        state = SimulationState(
            total_spend=2500.0,
        )

        goal = make_conversion_goal()

        evaluation = evaluate_goal(
            db,
            state,
            goal,
        )

        assert evaluation.status == GoalStatus.FAILED
        assert evaluation.budget_remaining == -500.0

    finally:
        db.close()


def test_goal_fails_at_deadline_without_target() -> None:
    """
    A goal fails if its deadline arrives before the target is reached.
    """

    db = SessionLocal()

    try:
        state = SimulationState(
            current_day=30,
        )

        goal = make_conversion_goal()

        evaluation = evaluate_goal(
            db,
            state,
            goal,
        )

        assert evaluation.status == GoalStatus.FAILED
        assert evaluation.days_remaining == 0

    finally:
        db.close()