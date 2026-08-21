"""
Autonomous executuon loop for our GoalOps business operator

1. Groq/LLM decides what should happen next
2. The MCP client executes allowed business tools
3. Pyhton objectively evaluates whether the business goal is complete

The loop will continue until the goal is achieved, failed or the 
maximum number of iterations is reached
"""

import json
from dataclasses import dataclass, field
from typing import Any

from app.mcp.client import GoalOpsMCPClient
from app.operator.llm import LLMClient
from app.operator.schemas import (
    OperatorAction,
    OperatorDecision,
)




@dataclass
class OperatorRunState:
    """
    Stores observable history for one autonomous operator run

    iteration:
        Number of llm decisions executed till now

    observations:
        Results returned by the MCP tools

    decisions:
        Structured decisions produced by the LLM

    final_goal_status:
        Latest objective goal evaluation returned by the MCP server

        This is stored so we can evaluate the complete run after the 
        operator stops

    """

    iteration: int = 0

    observations: list[dict[str, Any]] = field(
        default_factory=list,
    )

    decisions: list[OperatorDecision] = field(
        default_factory=list,
    )

    final_goal_status: dict[str, Any] | None = None








def build_operator_context(
        run_state: OperatorRunState,
        goal_status: dict[str, Any],
) -> str:
    """
    Build the information supplied to groq for it's next decision

    The LLM recieves only observable information

    Hidden simulation traits such integration_difficulty and hidden
    probability coefficients are delibrately excluded
    """

    context = {
        'business_goal':{
            'metric_name': goal_status['metric_name'],
            'target_value': goal_status['target_value']
        },
        'current_goal_status': goal_status,
        'iteration': run_state.iteration,
        'previous_observations': run_state.observations,
    }

    return json.dumps(
        context,
        indent=2,
    )







async def execute_decision(
        mcp_client: GoalOpsMCPClient,
        decision: OperatorDecision,
) -> dict[str, Any]:
    """
    Translate one LLM decision into one MCP tool call.

    The llm chooses the high level action

    This function controls which MCP tool is actually allowed to execute 
    that action
    """

    if (
        decision.action
        == OperatorAction.INSPECT_BUSINESS
        ):
        result = await mcp_client.call_tool(
            "business_snapshot"
        )

        return {
            'action': decision.action.value,
            'result': result,
        }


    if (
        decision.action
        == OperatorAction.INSPECT_INTERVENTIONS
    ):
        result = await mcp_client.call_tool(
            "available_interventions"
        )

        return {
                    'action': decision.action.value,
                    'result': result,
                }



    if (
            decision.action
            == OperatorAction.LAUNCH_INTERVENTION
        ):
        if not decision.intervention_name:
            raise ValueError(
                "launch_intervention requires "
                "intervention_name"
            )

        result = await mcp_client.call_tool(
            "run_intervention",
            {
                "intervention_name": decision.intervention_name,
            }
        )

        return {
            'action': decision.action.value,
            'intervention_name': (
                decision.intervention_name
            ),
            'result': result,
        }



    if  (
        decision.action
        == OperatorAction.ADVANCE_TIME
    ):
        if decision.days <= 0:
            raise ValueError(
                "advance_time requires days > 0"
            )

        result = await mcp_client.call_tool(
            'advance_time',
            {
                'days': decision.days,
            }
        )

        return {
            "action": decision.action.value,
            "days": decision.days,
            "result": result,
        }



    if (
        decision.action
        == OperatorAction.CHECK_GOAL
    ):

        result = await mcp_client.call_tool(
            "goal_status"
        )

        return {
            "action": decision.action.value,
            "result": result,
        }


    raise ValueError(
        f"Unsupported operator action: "
        f"{decision.action}"
    )

















async def run_operator(
        max_iterations: int = 10,
) -> OperatorRunState:
    """
    Runs one autonomous business goal attempt

    Every iteration:

    1. Python checks the goal
    2. Groq chooses the next action
    3. The actions gets executed through MCP
    4. The result becomes a new observation
    5. Groq recieves that observation on the next iteration

    The run stops when the goal succeeds, fails, or reaches the
    maximum iteration limit.
    """

    llm = LLMClient()

    run_state = OperatorRunState()

    async with GoalOpsMCPClient() as mcp_client:

        while (
            run_state.iteration
            < max_iterations
        ):
            # -------------------------------------------------
            # STEP 1: OBJECTIVE GOAL CHECK
            # -------------------------------------------------

            goal_status = await mcp_client.call_tool(
                'goal_status'
            )
            run_state.final_goal_status = goal_status

            print(
                f"\n=== ITERATION "
                f"{run_state.iteration + 1} ==="
            )

            print(
                "Goal status:",
                goal_status["status"],
            )

            print(
                "Current metric:",
                goal_status["current_value"],
            )

            print(
                "Budget remaining:",
                goal_status["budget_remaining"],
            )

            print(
                "Days remaining:",
                goal_status["days_remaining"],
            )

            if goal_status['status'] in {
                'achieved',
                'failed',
            }:
                print(
                    "\nOperator stopped:",
                    goal_status['status'],
                )
                break


            # -------------------------------------------------
            # STEP 2: BUILD LLM CONTEXT
            # -------------------------------------------------

            context = build_operator_context(
                run_state=run_state,
                goal_status=goal_status,
            )

            # -------------------------------------------------
            # STEP 3: ASK GROQ WHAT TO DO
            # -------------------------------------------------

            decision = llm.choose_next_action(
                context
            )

            run_state.decisions.append(
                decision
            )

            print(
                "\nDecision:",
                decision.action.value,
            )

            print(
                "Reason:",
                decision.reasoning_summary,
            )

            if decision.intervention_name:

                print(
                    "Intervention:",
                    decision.intervention_name,
                )

            if decision.days:

                print(
                    "Days:",
                    decision.days,
                )

            # -------------------------------------------------
            # STEP 4: EXECUTE THROUGH MCP
            # -------------------------------------------------

            observation = await execute_decision(
                mcp_client,
                decision,
            )

            run_state.observations.append(observation)

            print(
                "\nObservation:"
            )

            print(
                json.dumps(
                    observation,
                    indent=2,
                )
            )


            run_state.iteration += 1

        else:

            print(
                "\nOperator stopped because "
                "max_iterations was reached"
            )

    return run_state

    