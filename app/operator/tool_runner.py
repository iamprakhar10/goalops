"""
MCP-driven autonomous execution loop for GoalOps

Unlike our previous runner.py this runnr will not contain a hardcoded
OperatorAction-to-tool mapping.

Instead:

1. MCP exposes the available tools
2. The operator discoveres them using list_tools()
3. MCP tool schemas are converted into Groq tool definitions
4. Groq selects tools directly
5. The selected tool name and arguments are forwarded back to MCP
"""

import json
from typing import Any
from dataclasses import dataclass, field

from app.mcp.client import GoalOpsMCPClient
from app.operator.llm import LLMClient
from app.operator.tool_adapter import (
    mcp_tools_to_groq,
)
from app.mcp.tools import complete_business_run







@dataclass
class ToolOperatorRunState:
    """
    Stores the trace of one MCP-native autonomous operator run

    run_id:
        Persistent simulation run controlled by this operator.

    tool_calls:
        Every MCP tool call actually executed by the agent.

    final_goal_status:
        Final deterministic goal evaluation.

    rounds:
        Number of LLM tool-selection rounds completed.

    termination_reason:
        The reason why the operator terminated the flow
    """

    run_id: int | None=None

    tool_calls: list[dict[str, Any]] = field(
        default_factory=list,
    )

    final_goal_status: dict[str, Any] | None = None

    rounds: int = 0

    # Why this operator session stopped
    #termination_reason: str | None = None












async def run_tool_operator(
        *,
        max_tool_rounds: int,
        random_seed: int | None = None,
        run_id: int | None = None,
) -> ToolOperatorRunState:
    """
    Run one MCP-discovered GoalOps agent session.

    The application creates and owns the simulation run.

    MCP provides the available business tools.

    Groq chooses which discovered tool to call.

    Python executes the tool through MCP and determines objectively
    when the business goal has been achieved or failed.
    """

    llm = LLMClient()
    run_state = ToolOperatorRunState()

    resumed = run_id is not None

    if run_id is None and random_seed is None:
        random_seed = 42

    if run_id is not None and random_seed is not None:
        raise ValueError(
            "Provide either run_id to resume an existing run "
            "or random_seed to create a new run"
        )

    async with GoalOpsMCPClient() as mcp_client:

        # -----------------------------------------------------
        # CREATE OR RESUME A PERSISTENT SIMULATION RUN
        # -----------------------------------------------------

        if run_id is None:

            run_result = await mcp_client.call_tool(
                "create_run",
                {
                    "random_seed": random_seed,
                },
            )

            run_id = run_result["run_id"]

            print(
                f"\nCreated simulation run: {run_id}"
            )

        else:

            initial_status = await mcp_client.call_tool(
                "goal_status",
                {
                    "run_id": run_id,
                },
            )

            if initial_status["status"] in {
                "achieved",
                "failed",
            }:
                raise ValueError(
                    f"Simulation run {run_id} is already "
                    f"{initial_status['status']}."
                )

            print(
                f"\nResuming simulation run: {run_id}"
            )

        # Works for both new and resumed runs.
        run_state.run_id = run_id

        # -----------------------------------------------------
        # DISCOVER TOOLS FROM MCP
        # -----------------------------------------------------

        mcp_tools = await mcp_client.list_tools()

        agent_tools = [
            tool
            for tool in mcp_tools.tools
            if tool.name != "create_run"
        ]

        groq_tools = mcp_tools_to_groq(
            agent_tools
        )

        # -----------------------------------------------------
        # INITIAL LLM CONTEXT
        # -----------------------------------------------------

        messages: list[Any] = [
            {
                "role": "system",
                "content": (
                    "You are an autonomous business operator "
                    "inside a simulated B2B SaaS company.\n\n"

                    "Your objective is to increase trial-to-paid "
                    "conversion to at least 40% within 30 simulated "
                    "days while spending no more than 2000.\n\n"

                    "Use the available tools to investigate the "
                    "business, inspect interventions, take actions, "
                    "advance simulated time, and check progress.\n\n"

                    "Use business evidence before making important "
                    "decisions. Do not invent tool results. "
                    "Do not claim an intervention worked until its "
                    "result has been observed."
                ),
            },
            {
                "role": "user",
                "content": (
                    (
                        f"Resume operating simulation run {run_id}. "
                        "Inspect the current business state before taking "
                        "further action."
                    )
                    if resumed
                    else
                    (
                        f"Begin operating simulation run {run_id}. "
                        "Work autonomously toward the business goal."
                    )
                ),
            },
        ]

        # -----------------------------------------------------
        # AGENT LOOP
        # -----------------------------------------------------

        for round_number in range(
            1,
            max_tool_rounds + 1,
        ):

            run_state.rounds = round_number

            print(
                f"\n=== TOOL ROUND {round_number} ==="
            )

            response = llm.create_tool_call_response(
                messages=messages,
                tools=groq_tools,
            )

            assistant_message = (
                response
                .choices[0]
                .message
            )

            # Save the assistant message because Groq requires
            # the tool-call message to remain in conversation
            # history before tool results are returned.
            messages.append(
                assistant_message
            )

            tool_calls = (
                assistant_message.tool_calls
                or []
            )

            # -------------------------------------------------
            # MODEL DID NOT REQUEST A TOOL
            # -------------------------------------------------

            if not tool_calls:

                print(
                    "\nLLM final response:"
                )

                print(
                    assistant_message.content
                )

                # We still perform an objective final goal check.
                #
                # The LLM does not decide whether the run actually
                # succeeded.
                final_goal_status = await mcp_client.call_tool(
                    "goal_status",
                    {
                        "run_id": run_id,
                    },
                )

                run_state.final_goal_status = (
                    final_goal_status
                )

                if final_goal_status["status"] in {
                    "achieved",
                    "failed",
                }:

                    complete_business_run(
                        run_id=run_id,
                        status=final_goal_status["status"],
                    )

                    return run_state

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The goal is still in progress. "
                            "Continue operating using the available tools."
                        ),
                    }
                )

                continue

            # -------------------------------------------------
            # EXECUTE EVERY TOOL CALL THROUGH MCP
            # -------------------------------------------------

            for tool_call in tool_calls:

                tool_name = (
                    tool_call.function.name
                )

                arguments = json.loads(
                    tool_call.function.arguments
                )

                # -------------------------------------------------
                # FORCE THE CORRECT RUN ID
                # -------------------------------------------------
                #
                # Run identity belongs to the application,
                # not the LLM.

                if "run_id" in arguments:
                    arguments["run_id"] = run_id

                print(
                    "\nTool:",
                    tool_name,
                )

                print(
                    "Arguments:",
                    arguments,
                )

                # -------------------------------------------------
                # EXECUTE THROUGH MCP
                # -------------------------------------------------

                result = await mcp_client.call_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                )

                print(
                    "Result:",
                    json.dumps(
                        result,
                        indent=2,
                    ),
                )

                # -------------------------------------------------
                # RECORD WHAT ACTUALLY HAPPENED
                # -------------------------------------------------

                run_state.tool_calls.append(
                    {
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result,
                    }
                )

                # Feed the real MCP result back to Groq.
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": (
                            tool_call.id
                        ),
                        "name": tool_name,
                        "content": json.dumps(
                            result
                        ),
                    }
                )

                if tool_name == "goal_status":

                    run_state.final_goal_status = (
                        result
                    )

                    if result["status"] in {
                        "achieved",
                        "failed",
                    }:

                        complete_business_run(
                            run_id=run_id,
                            status=result["status"],
                        )

                        print(
                            "\nOperator stopped:",
                            result["status"],
                        )

                        return run_state

        # -----------------------------------------------------
        # MAX TOOL ROUNDS REACHED
        # -----------------------------------------------------

        print(
            "\nOperator stopped because the maximum "
            "tool-round limit was reached."
        )

        # Always finish with an objective goal evaluation.
        final_goal_status = await mcp_client.call_tool(
            "goal_status",
            {
                "run_id": run_id,
            },
        )

        run_state.final_goal_status = (
            final_goal_status
        )

        if final_goal_status["status"] in {
            "achieved",
            "failed",
        }:

            complete_business_run(
                run_id=run_id,
                status=final_goal_status["status"],
            )

        return run_state