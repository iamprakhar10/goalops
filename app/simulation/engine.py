"""
Business simulation engine for our fake SaaS company

This module advances simulated time and applies predefined business
rules to customer companies

The sumulator will decide the consequences if interventions, not AI

Th aotonomous oerator will eventually be allowed to choose actions,
but it will not be allowed to directly modify customer outcomes
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    Customer,
    CustomerEvent,
    SupportTicket,
)

from app.simulation.state import SimulationState



















GUIDED_INTEGRATION_HELP = "guided_integration_help"


SIMULATION_START_DATE = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)








def activate_intervention(
        state:SimulationState,
        intervention_name: str,
) -> None:
    """
    Activates a business intervention in simulation

    For now we support only:

        guided_integration_help

    Later this function can validate a larger catalog of actions.
    """

    allowed_interventions = {
        GUIDED_INTEGRATION_HELP,
    }

    if intervention_name not in allowed_interventions:
        raise ValueError(
            f"Unknown intervention: {intervention_name}"
        )

    state.active_interventions.add(
        intervention_name
    )











def customer_has_event(
        db: Session,
        customer_id: int,
        event_name: str,
) -> bool:
    """
    Return whether a customer company already has a lifecycle event

    This will prevent milestone events such as completed_onboarding from 
    being inserted more than once
    """

    statement = (
        select(CustomerEvent.id)
        .where(
            CustomerEvent.customer_id == customer_id,
            CustomerEvent.event_name == event_name,
        )
        .limit(1)
    )

    return db.scalar(statement) is not None










def add_customer_event(
        db: Session,
        customer_id: int,
        event_name: str,
        occurred_at: datetime,
) -> None:
    """
    Adds a company lifecycle event if it doesn't already exist

    Company lifecycle milestones should normally appear only once
    for the current customer journey.
    """

    if customer_has_event(
        db=db,
        customer_id=customer_id,
        event_name=event_name,
    ):
        return 

    db.add(
        CustomerEvent(
            customer_id=customer_id,
            event_name=event_name,
            occurred_at=occurred_at,
        )
    )








def get_integration_problem_customers(
        db: Session,
) -> list[Customer]:
    """
    Returns trial customer companies with an integration support
    problem

    These companies are our current target population for the guided 
    itegration intervention
    """

    statement =  (
        select(Customer)
        .join(
            SupportTicket,
            SupportTicket.customer_id == Customer.id,
        )
        .where(
            Customer.status == "trial",
            SupportTicket.category == "integration",
        )
        .distinct()
    )

    return list(
        db.scalars(statement).all()
    )












def apply_guided_integration_help(
        db: Session,
        state: SimulationState,
) -> None:
    """
    Applying the first simulated intervention

    Business rule for v1:

    If guided integration help is active, trial companies that have
    integration problems will become eligible to progress

    To keep the first simulator deterministic and testable:

    - first 4 eligible companies complete onboarding
    - first 2 of those companies convert to paid

    Later this deterministic rule will be replaced by probabilistic
    behavior and richer customer characteristics.
    """

    if GUIDED_INTEGRATION_HELP not in state.active_interventions:
        return

    customers = get_integration_problem_customers(db)

    current_time = (
        SIMULATION_START_DATE
        + timedelta(days=state.current_day)
    )

    # First four eligible companies successfull completd onboarding
    onboarding_customers = customers[:4]

    for customer in onboarding_customers:
        add_customer_event(
            db=db,
            customer_id=customer.id,
            event_name="completed_onboarding",
            occurred_at=current_time,
        )


    # Of those four companies, two subsequently convert to paid.
    converting_customers = onboarding_customers[:2]

    for customer in converting_customers:
        customer.status = "paid"

        add_customer_event(
            db,
            customer.id,
            "converted_to_paid",
            current_time,
        )











def advance_days(
        db: Session,
        state: SimulationState,
        days: int,
) -> None:
    """
    Advance the fake business clock and applies active simulation
    rules

    Ofcoulrse no real world waiting will happen

    Eg.
        advance_days(db, state, 7)

    immediately moves the simulated business seven days into 
    the future.
    """

    if days <= 0:
        raise ValueError(
            "Days must be greater than zero"
        )

    state.current_day += days

    apply_guided_integration_help(
        db,
        state,
    )

    db.flush()