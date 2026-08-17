"""
Business simulation engine for our fake SaaS company

This module advances simulated time and applies predefined business
rules to customer companies

The sumulator will decide the consequences if interventions, not AI

Th aotonomous oerator will eventually be allowed to choose actions,
but it will not be allowed to directly modify customer outcomes
"""
import random

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    Customer,
    CustomerEvent,
    SupportTicket,
    CustomerSimulationProfile,
)

from app.simulation.state import SimulationState



















GUIDED_INTEGRATION_HELP = "guided_integration_help"


SIMULATION_START_DATE = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)









def clamp_probability(
     probability: float,   
) -> float:
    """
    Restricting probability from 0 to 1
    """

    return max(
        0.0,
        min(1.0, probability)
    )





















def calculate_onboarding_probability(
    profile: CustomerSimulationProfile,
    guided_integration_help_active: bool,
) -> float:
    """
    Calculate the probability that a stalled customer completes onboarding.

    Higher customer intent and engagement increase the probability.

    Greater integration difficulty decreases it.

    Guided integration help significantly reduces the practical effect
    of integration friction.

    These coefficients define part of the hidden causal structure of
    our simulated business world.
    """

    probability = (
        0.15
        + (0.35 * profile.intent_score)
        + (0.25 * profile.engagement_score)
        - (0.45 * profile.integration_difficulty)
    )

    if guided_integration_help_active:
        probability += 0.45

    return clamp_probability(
        probability
    )



















def calculate_conversion_probability(
        profile: CustomerSimulationProfile,
) -> float:
    """
    Calculates the probability that an onboarded trial company converts
    to a paid customer

    Intent and engagement make conversion more likely
    """

    probability = (
        .1
        + (.45* profile.intent_score)
        + (.3* profile.engagement_score)
    )

    return clamp_probability(
        probability
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
        .order_by(
            Customer.id
        )
        .distinct()
    )
    # The order_by(Customer.id) helps make benchmark runs 
    # reproducible

    return list(
        db.scalars(statement).all()
    )













def apply_guided_integration_help(
        db: Session,
        state: SimulationState,
) -> None:
    """
    Simulate customer outcomes when guided integration help is active

    Eligible companies are evaluated INDEPENDENTLY

    For each company:
    1. Calculate it's onboarding probability
    2. Randomly determine whether onboarding succeded
    3. If onboarding succeeds, calculate conversion probability
    4. Randomly determine whether the company becomes paid
    """

    if GUIDED_INTEGRATION_HELP not in state.active_interventions:
        return

    customers = get_integration_problem_customers(db)

    current_time = (
        SIMULATION_START_DATE
        + timedelta(days=state.current_day)
    )

    # A deterministic seed means identical benchmark runs produce
    # identical random outcomes.
    random_generator = random.Random(
        state.random_seed + state.current_day
    )

    newly_onboarded: list[
        tuple[Customer, CustomerSimulationProfile]
    ] = []


    # ---------------------------------------------------------
    # ONBOARDING
    # ---------------------------------------------------------

    for customer in customers:
        profile = customer.simulation_profile

        if profile is None:
            continue

        probability = calculate_onboarding_probability(
            profile,
            guided_integration_help_active=True,
        )

        random_draw = random_generator.random()

        if random_draw < probability:

            add_customer_event(
                db,
                customer.id,
                "completed_onboarding",
                current_time,
            )

            newly_onboarded.append(
                (
                    customer,
                    profile,
                )
            )


    # ---------------------------------------------------------
    # PAID CONVERSION
    # ---------------------------------------------------------

    for customer, profile in newly_onboarded:

        probability = calculate_conversion_probability(
            profile
        )

        random_draw = random_generator.random()
        if random_draw < probability:

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


















