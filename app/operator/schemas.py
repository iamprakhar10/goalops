"""
Structured data models used by the autonomous business operator.

This module defines the EXACT shapes of decisions returned by the LLM

The LLM is not allowed to return arbitrary instructions that our 
application blindly executes. It's output will be validated before 
GoalOps accepts the decision
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict




class OperatorAction(str, Enum):
    """
    High-leevel actiosn the operator may choose at this stage

    These are limited

    Later we will add actual MCP tool calling with more precise tool
    names and arguments
    """

    INSPECT_BUSINESS = "inspect_business"
    INSPECT_INTERVENTIONS = "inspect_interventions"
    LAUNCH_INTERVENTION = "launch_intervention"
    ADVANCE_TIME = "advance_time"
    CHECK_GOAL = "check_goal"










class OperatorDecision(BaseModel):
    """
    Represents one structured decision produced by the LLM.

    action:
        High-level next action the operator wants to take.

    reasoning_summary:
        Short explanation of why that action is appropriate.

        This is not hidden chain-of-thought. It is a concise,
        user-visible justification for the decision.

    intervention_name:
        Name of an intervention when the chosen action is
        launch_intervention.

        For other actions this is an empty string.

    days:
        Number of simulated days to advance when action is advance_time.

        For other actions this is zero.
    """
    # No surprise fields allowed.
    model_config = ConfigDict(
        extra='forbid',
    )

    action: OperatorAction

    reasoning_summary: str

    intervention_name: str

    days: int