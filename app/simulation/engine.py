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

from app.simulation.interventions import (
    ActiveIntervention,
    InterventionDefinition,
    get_intervention,
)




















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
    intervention: InterventionDefinition,
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
        + intervention.onboarding_bonus
    )

    return clamp_probability(
        probability
    )



















def calculate_conversion_probability(
        profile: CustomerSimulationProfile,
        intevention: InterventionDefinition,
) -> float:
    """
    Calculates the probability that an onboarded trial company converts
    to a paid customer

    Strong customer Intent and engagement make conversion more likely

    Some interventions may also provide a conversion bonus
    """

    probability = (
        .1
        + (.45* profile.intent_score)
        + (.3* profile.engagement_score)
        + intevention.conversion_bonus
    )

    return clamp_probability(
        probability
    )





















def get_eligible_trial_customers(
        db: Session,
        run_id: int,
        intervention: InterventionDefinition,
) -> list[Customer]:
    """
    Returns list of trial companies eligible for a particular 
    intervention

    If intervention targest a support-ticket category, only companies
    with that problems are selected

    Otherwise, trial companies that have started onboarding are eligible
    """
    statement = (
        select(Customer)
        .where(
            Customer.status == "trial",
            Customer.simulation_run_id == run_id,
        )
        .order_by(
            Customer.id
        )
    )

    if intervention.target_ticket_category is not None:

        statement = (
            statement
            .join(
                SupportTicket,
                SupportTicket.customer_id == Customer.id,
            )
            .where(
                SupportTicket.category
                == intervention.target_ticket_category
            )
            .distinct()
        )

    customers = list(
        db.scalars(statement).all()
    )

    eligible_customers: list[Customer] = []

    for customer in customers:
        if customer_has_event(
            db,
            customer.id,
            "started_onboarding",
        ):
            eligible_customers.append(
                customer
            )

    return eligible_customers
















def activate_intervention(
        state:SimulationState,
        intervention_name: str,
) -> ActiveIntervention:
    """
    Activates a business intervention in simulation

    The intervention definition will determine it's cost and duration

    Launching an intervention doesn't directly change customer companies
    behaviour/outcome. It only creates an active intervention whose 
    effects will later be evaluated by the simulation engine
    """

    definition = get_intervention(
        intervention_name
    )

    if intervention_name in state.active_interventions:
        raise ValueError(
            f"Intervention already active: {intervention_name}"
        )

    active_intervention = ActiveIntervention(
        name=definition.name,
        started_day=state.current_day,
        evaluation_day=(
            state.current_day
            + definition.duration_days
        ),
    )

    state.active_interventions[
        intervention_name
    ] = active_intervention

    state.total_spend += definition.cost

    return active_intervention









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
        run_id: int,
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
            Customer.simulation_run_id == run_id,
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













def evaluate_intervention(
        db: Session,
        run_id: int,
        state: SimulationState,
        active_intervention: ActiveIntervention,
) -> None:
    """
    Evaluates the outcome of one complete business intervention.

    Eligible companies are evaluated indepndently

    The intervention will modify probabilities, while hidden customer
    traits and randomness determine the actual outcome.
    """

    intervention = get_intervention(
        active_intervention.name
    )

    customers = get_eligible_trial_customers(
        db=db,
        run_id=run_id,
        intervention=intervention,
    )

    current_time = (
        SIMULATION_START_DATE
        + timedelta(
            days=active_intervention.evaluation_day
        )
    )

    random_generator = random.Random(
        state.random_seed
        + active_intervention.evaluation_day
    )

    newly_onboarded: list[
        tuple[
            Customer,
            CustomerSimulationProfile,
        ]
    ] = []

    # ---------------------------------------------------------
    # ONBOARDING OUTCOME
    # ---------------------------------------------------------

    for customer in customers:
        # we won't complete onboarding twice
        if customer_has_event(
            db,
            customer.id,
            'completed_onboarding',
        ):
            continue

        profile = customer.simulation_profile

        if profile is None:
            continue

        probability = calculate_onboarding_probability(
            profile=profile,
            intervention=intervention,
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
    # PAID CONVERSION OUTCOME
    # ---------------------------------------------------------

    for customer, profile in newly_onboarded:
        probability = calculate_conversion_probability(
            profile,
            intervention,
        )

        random_draw = random_generator.random()

        if random_draw < probability:
            customer.status = 'paid'
            add_customer_event(
                db,
                customer.id,
                "converted_to_paid",
                current_time,
            )












def advance_days(
        db: Session,
        run_id: int,
        state: SimulationState,
        days: int,
) -> None:
    """
    Advance the fake business clock and applies active simulation
    rules

    Any intervention whose evaluation day is reached during the time
    jump is evaluated 

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

    target_day = (
        state.current_day + days
    )

    completed_interventions: list[str] = []

    for (
        intevention_name,
        active_intervention,
    ) in state.active_interventions.items():

        if (
            active_intervention.evaluation_day
            <= target_day
        ):
            evaluate_intervention(
                db,
                run_id,
                state,
                active_intervention,
            )

            completed_interventions.append(
                intevention_name
            )

    # Removing interventions whose outcomes have now been evaluated.
    for intevention_name in completed_interventions:

        del state.active_interventions[
            intevention_name
        ]

    state.current_day = target_day

    db.flush()


















