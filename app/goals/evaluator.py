"""
Goal Evaluation logic for the autonomous business operator

This module measures the current cimulated business state and
determines whether a business goal is still in progress, achieved
or failed

The evaluator is deterministic in nature, LLM won't decide whether a 
intervention worked or not
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.goals.models import BusinessGoal, GoalStatus
from app.services.analytics import get_conversion_rate
from app.simulation.state import SimulationState









@dataclass(frozen=True)
class GoalEvaluation:
    """
    Result of evaluating one business goal
    current_value:
        Current measured value of the goal metric.

    status:
        Whether the goal is achieved, failed, or still in progress.

    budget_remaining:
        Simulated intervention budget still available.

    days_remaining:
        Simulated days remaining before the deadline.
    """

    current_value: float
    status: GoalStatus
    budget_remaining: float
    days_remaining: int











def get_goal_metric_value(
        db: Session,
        metric_name: str,
) -> float:
    """
    Returns the current value of a business metric

    For first benchmark GoalOps supports only trial to paid conversions

    More metrics like churn, activation and retentions will be added 
    later
    """

    if metric_name == "trial_to_paid_conversion":
        return get_conversion_rate(db)

    raise ValueError(
        f"Unsupported goal metric: {metric_name}"
    )












def evaluate_goal(
        db:Session,
        state: SimulationState,
        goal: BusinessGoal,
) -> GoalEvaluation:
    """
    Evaluate whether a business goal has been achieved or failed

    Evaluation Rules:
    1. If spending exceeds the budget, the goal fails.
    2. If the target metric is reached within budget, the goal succeeds.
    3. If the deadline has passed without success, the goal fails.
    4. Otherwise the goal remains in progress.
    """

    current_value = get_goal_metric_value(
        db,
        goal.metric_name,
    )

    budget_remaining = (
        goal.max_budget
        - state.total_spend
    )

    days_remaining = max(
        0,
        goal.deadline_day - state.current_day,
    )

     # Budget constraint violated.
    if state.total_spend > goal.max_budget:
        status = GoalStatus.FAILED

    # Metric target reached within constraints.
    elif current_value >= goal.target_value:
        status = GoalStatus.ACHIEVED

    # Deadline reached or exceeded without hitting target.
    elif state.current_day >= goal.deadline_day:
        status = GoalStatus.FAILED

    else:
        status = GoalStatus.IN_PROGRESS

    return GoalEvaluation(
        current_value=current_value,
        status=status,
        budget_remaining=budget_remaining,
        days_remaining=days_remaining,
    )











