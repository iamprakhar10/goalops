"""
Groq LLM client for our autonomous business-goal operator

This module isolates all communication with groq from rest of GoalOps

Other parts of application should not create Groq clients directly.
They sue LLMClient instead

This makes it easier to repace groq in future if needed
"""


import json
import os

from typing import Any
from dotenv import load_dotenv
from groq import Groq
from groq import  BadRequestError
 
from app.operator.prompts import OPERATOR_SYSTEM_PROMPT
from app.operator.schemas import OperatorDecision







load_dotenv()



class LLMClient:
    """
    Small abstraction around the Groq API.

    The client is responsible for:

    - loading Groq configuration
    - sending prompts
    - requesting structured output
    - validating the returned decision

    It does not execute business actions.
    """

    def __init__(self) -> None:
        """
        Create the Groq client from environment configuration.
        """

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured"
            )

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )

        self.client = Groq(
            api_key=api_key,
        )



    def choose_next_action(
            self,
            context: str,
    ) -> OperatorDecision:
        """
        Asks the LLM to choose the operator's next high-level action.

        The respomse is constrained to the OperatorDecision JSON schema

        Args:
            context:
                Observable information currently available to the operator
                such as it's goal or business metrics

        Returns:
            A validated OperatorDecision object.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    'role': "system",
                    'content': OPERATOR_SYSTEM_PROMPT,
                },
                {
                    'role': 'user',
                    'content': context,
                },
            ],
            response_format={
                'type': 'json_schema',
                'json_schema': {
                    'name': 'operator_decision',
                    'strict': True,
                    'schema': OperatorDecision.model_json_schema(),
                },
            },
        )

        content = (
            response
            .choices[0]
            .message
            .content
        )

        if content is None:
            raise RuntimeError(
                "Groq returned an empty response"
            )

        response_data = json.loads(
            content
        )

        return OperatorDecision.model_validate(
            response_data
        )


    def create_tool_call_response(
            self,
            messages: list[dict[str, Any]],
            tools: list[dict[str, Any]],
    ):
        """
        Ask Groq to choose whether to call one or more available tools

        The tool definitions come directly from the MCP server

        Grok does not execute the tools. It only returns structures 
        tool-call requests containing:
        - tool name
        - tool arguments
        - tool-call ID

        If Groq produces malformed tool-call output, we will retry a small
        number of times before giving up
        """
        max_attempts=3

        for attempt in range(max_attempts):
            try: 

                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice='auto',
                    temperature=.2,
                )

            except BadRequestError as exc:
                if (
                    "output_parse_failed"
                    not in str(exc)
                ):
                    raise

                if attempt == max_attempts-1:
                    raise

                print(
                    "=====>~GrOq produced an invaild tool call."
                    "Retrying..."
                )
        raise RuntimeError(
            "Groq tool-call generation failed unexpectedly."
        )
        










    