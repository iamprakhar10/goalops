"""
Business goal ddefinition for GoalOps

This module defines measurable objectives which our autonomous
operator must use/achieve/persue inside the simulated business

Goals contain explicit metrics, targets, deadlines, and budget
constraints so success can objectively be defined by our python code 
rather than by AI/LLM
"""

from dataclasses import dataclass
from enum import Enum




class GoalStatus(str, Enum):
    """
    Possible states of a business goal
    """

    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    FAILED = "failed"










@dataclass(frozen=True)
class BusinessGoal:
    """
    Represents one measurable business objective

    metric_name:
        Business metric being optimized

    target_value:
        Minimum metric value required for success

    deadline_day:
        Simulated day by which the target must be achieved

    max_budget:
        Maximum allowed intervention spending
    """

    metric_name: str
    target_value: float
    deadline_day: int
    max_budget: float