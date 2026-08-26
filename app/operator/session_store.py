"""
Persistence helpers for autonomous operator sessions and tool calls

A simulation run can span multipule Operator sessions when execution
stops and is later resumed

This module stores:
- when an operator sesion starts
- every MCP tool call made with arguments during that session
- Why the session ended
- And the complete sesion history for a simulation run.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    OperatorToolCall,
    OperatorSession,
)











def create_operator_session(
        db: Session,
        simulation_run_id: int,
) -> OperatorSession:
    """
    Create a new operator session for one simulation run
    Remember, one simulation run can have multiple OperatorSession

    This represnts one invocation pf run_tool_operator()

    The function flushes instead of commiting so the caller owns
    the surrounding transaction.
    """

    operator_session = OperatorSession(
        simulation_run_id=simulation_run_id,
    )

    db.add(
        operator_session
    )

    db.flush()

    return operator_session












def save_operator_tool_call(
        db: Session,
        operator_session_id: int,
        sequence_number: int,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
) -> OperatorToolCall:
    """
    Perssist one MCP tool call made during an operator session

    Sequence_number preserves the order in which tools were executed
    inside the session
    """
    tool_call = OperatorToolCall(
        operator_session_id=operator_session_id,
        sequence_number=sequence_number,
        tool_name=tool_name,
        arguments=arguments,
        result=result,
    )

    db.add(
        tool_call
    )

    db.flush()

    return tool_call








def complete_operator_session(
        db: Session,
        operator_session_id: int,
        termination_reason: str,
) -> OperatorSession:
    """
    Mark an operator session as completed

    etrmination_reason describes why this particular operator session 
    stopped, not the final lifetime state of the simulation run
    """
    allowed_reasons = {
        'goal_achieved',
        'goal_failed',
        'max_tool_rounds',
        "execution_error",
    }

    if termination_reason not in allowed_reasons:
        raise ValueError(
            f"Unsupported termination reason: {termination_reason}"
        )

    operator_session = db.get(
        OperatorSession,
        operator_session_id,
    )

    if operator_session is None:
        raise ValueError(
            f"Operator session {operator_session_id} does ont exist."
        )
    operator_session.termination_reason = (
        termination_reason
    )

    operator_session.completed_at=(
        datetime.now(timezone.utc)
    )

    db.flush()

    return operator_session














def get_operator_sessions_for_run(
        db: Session,
        simulation_run_id: int,
) -> list[OperatorSession]:
    """
    Return every operator session belonging to one simulation run

    Sessions are returned in creation order
    """

    statement = (
        select(OperatorSession)
        .where(
            OperatorSession.simulation_run_id
            == simulation_run_id
        )
        .order_by(
            OperatorSession.id
        )
    )

    return list(
        db.scalars(statement).all()
    )












def get_operator_tool_calls_for_run(
        db: Session,
        simulation_run_id: int,
) -> list[OperatorToolCall]:
    """
    Return every persisted operator tool call for a simulation run.

    Calls are ordered first by operator session and then by their 
    sequence number within that session
    """

    statement = (
        select(OperatorToolCall)
        .join(
            OperatorSession,
            OperatorToolCall.operator_session_id
            == OperatorSession.id,
        )
        .where(
            OperatorSession.simulation_run_id
            == simulation_run_id
        )
        .order_by(
            OperatorSession.id,
            OperatorToolCall.sequence_number,
        )
    )

    return list(
        db.scalars(statement).all()
    )
