"""
Manual smoke test for the GoalOps Groq integration.

This script sends the first benchmark goal to the LLM and prints the
structured action selected by the model.

It does not execute any business action or modify the simulation.
"""

from app.operator.llm import LLMClient


def main() -> None:
    """
    Ask Groq what the operator should do first.
    """

    llm = LLMClient()

    context = """
Business goal:

Increase trial-to-paid conversion to at least 40%.

Current baseline:
30%.

Deadline:
30 simulated days.

Maximum intervention budget:
2000.

You have not inspected the current business data yet.

Choose the next action.
"""

    decision = llm.choose_next_action(
        context
    )

    print(
        decision.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()