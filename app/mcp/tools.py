"""
Tool implementations exposed through the GoalOps MCP server

This module contains normal that will provide controlled access to 
business analytics, interventions, simulated time, and goal evaluation

These functions form boundary between our future autonomous operator
and the simulated SaaS company

The operator will ofc not recieve direct SQLAlchemy or postgreSQL access
"""

from app.database.db import SessionLocal
from app.goals.evaluator import evaluate_goal
from app.goals.models import BusinessGoal
from app.services.analytics import (
    get_conversion_rate,
    get_onboarding_funnel,
    get_product_usage_summary,
)
from app.services.support_analytics import get_support_summary
from app.simulation.engine import (
    activate_intervention,
    advance_days,
)
from app.simulation.interventions import (
    INTERVENTION_REGISTRY,
)
from app.simulation.state import SimulationState



# 
#  CURRENT VERSION
# ───────────────

# 1 running MCP server
# =
# 1 simulation

# Stop server
# =
# simulation state forgotten


# LATER VERSION
# ─────────────

# Many simulation runs

# Run 101
# Run 102
# Run 103

# stored in PostgreSQL

# Stop/restart server
# =
# runs are still there





# ---------------------------------------------------------
# ---------------------------------------------------------

# GLOBAL SIMULATION RUN
# ---------------------------------------------------------
# ---------------------------------------------------------
# For our first local MCP server, one server process represents one
# simulation run
# 
# Later we can introduce run IDs and persistent simulation state
# so multiple benchmark runs can exist independently 
simulation_state = SimulationState(
    random_seed=42,
)


# our first benchmark goal
business_goal = BusinessGoal(
    metric_name="trial_to_paid_conversion",
    target_value=40.0,
    deadline_day=30,
    max_budget=2000.0,
)





def get_business_snapshot() -> dict:
    """
    Returns the main observable state of the simulated business

    This is a read-only tool

    This will combine
    - conversion rate
    - onboarding funnel
    - product usage
    - support-ticket evidence
    - current simulated day
    - current intervention spending
    """

    db = SessionLocal()

    try:
        return {
            "current_day": simulation_state.current_day,
            "total_spend": simulation_state.total_spend,
            "conversion_rate": get_conversion_rate(db),
            "onboarding_funnel": get_onboarding_funnel(db),
            "product_usage": get_product_usage_summary(db),
            "support": get_support_summary(db),
        }

    finally:
        db.close()







def list_available_interventions() ->list[dict]:
    """
    Returns the interventions the operator is allowed to launch

    The operator can't invent arbitray simulator actions
    """

    return [
        {
            "name": intervention.name,
            "description": intervention.description,
            "cost": intervention.cost,
            "duration_days": intervention.duration_days,
        }
        for intervention in INTERVENTION_REGISTRY.values()
    ]









def launch_intervention(
        intervention_name: str,
) -> dict:
    """
    Activate one approved business intervention

    Launching intervention records its cost and duration but does not
    immediately create a successful business outcome
    """

    active_intervention = activate_intervention(
        simulation_state,
        intervention_name,
    )

    return {
        "name": active_intervention.name,
        "started_day": active_intervention.started_day,
        "evaluation_day": active_intervention.evaluation_day,
        "total_spend": simulation_state.total_spend,
    }











def advance_simulation(
        days: int,
) -> dict:
    """
    Advance the fake business clock

    When an active intervention reachesit's evaluation day, the simulation
    engine determines customer outcomes according to hidden traits,
    intervention effects, and probabilistic rules
    """
    db = SessionLocal()

    try:
        advance_days(
            db,
            simulation_state,
            days
        )

        # MCP actions represents real actions inside the simulation run
        # so the database changese must persist 
        db.commit()

        return {
            "current_day": simulation_state.current_day,
            "active_interventions": list(
                simulation_state.active_interventions.keys()
            ),
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()






def evaluate_business_goal() -> dict:
    """
    Evaluates the current benchmark goal objectively(Not using LLM)
    """

    db = SessionLocal()

    try:
        evaluation = evaluate_goal(
            db,
            simulation_state,
            business_goal,
        )

        return {
            "metric_name": business_goal.metric_name,
            "target_value": business_goal.target_value,

            "current_value": evaluation.current_value,
            "status": evaluation.status.value,

            "max_budget": business_goal.max_budget,
            "budget_remaining": evaluation.budget_remaining,

            "deadline_day": business_goal.deadline_day,
            "days_remaining": evaluation.days_remaining,
        }
    finally:
        db.close()