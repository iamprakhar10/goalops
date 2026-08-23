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
from app.simulation.run_store import (
    create_simulation_run,
    load_simulation_state,
    save_simulation_state,
)
from typing import Any

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

# simulation_state = SimulationState(
#     random_seed=42,
# )

# our first benchmark goal
business_goal = BusinessGoal(
    metric_name="trial_to_paid_conversion",
    target_value=40.0,
    deadline_day=30,
    max_budget=2000.0,
)





def get_business_snapshot(
        run_id: int,
) -> dict[str, Any]:
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

    state = load_simulation_state(
        db,
        run_id,
    )

    try:
        return {
            "current_day": state.current_day,
            "total_spend": state.total_spend,
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
        run_id: int,
        intervention_name: str,
) -> dict:
    """
    Activate one approved business intervention

    Launching intervention records its cost and duration but does not
    immediately create a successful business outcome
    """

    with SessionLocal() as db:
        try:
            state = load_simulation_state(
                db,
                run_id,
            )


            active_intervention = activate_intervention(
                state,
                intervention_name,
            )

            save_simulation_state(
                db,
                run_id,
                state,
            )

            db.commit()

            return {
                'run_id': run_id,
                "name": active_intervention.name,
                "started_day": active_intervention.started_day,
                "evaluation_day": active_intervention.evaluation_day,
                "total_spend": state.total_spend,
            }

        except Exception:
            db.rollback()
        raise











def advance_simulation(
        days: int,
        run_id: int,
) -> dict[str, Any]:
    """
    Advance one persistent simulation run
    """

    with SessionLocal() as db:

        try:
            state = load_simulation_state(
                db,
                run_id,
            )

            advance_days(
                db,
                state,
                days,
            )

            save_simulation_state(
                db, 
                run_id,
                state,
            )

            db.commit()

            return {
                'run_id': run_id,
                'current_day': state.current_day,
                'active_interventions': list(
                    state.active_interventions.keys()
                ),
            }

        except Exception:
            db.rollback()
            raise


# load run 17
# ↓
# day 0
# ↓
# advance 7
# ↓
# day 7
# ↓
# save run 17
# ↓
# commit


    # db = SessionLocal()

    # try:
    #     advance_days(
    #         db,
    #         simulation_state,
    #         days
    #     )

    #     # MCP actions represents real actions inside the simulation run
    #     # so the database changese must persist 
    #     db.commit()

    #     return {
    #         "current_day": simulation_state.current_day,
    #         "active_interventions": list(
    #             simulation_state.active_interventions.keys()
    #         ),
    #     }

    # except Exception:
    #     db.rollback()
    #     raise

    # finally:
    #     db.close()






def evaluate_business_goal(
        run_id: int,
) -> dict[str, Any]:
    """
    Evaluates the current benchmark goal objectively(Not using LLM)
    """

    with SessionLocal() as db:
        state = load_simulation_state(
            db,
            run_id,
        )

        evaluation = evaluate_goal(
            db,
            state,
            business_goal,
        )

        return {
            "run_id": run_id,
            "metric_name": business_goal.metric_name,
            "target_value": business_goal.target_value,
            "current_value": evaluation.current_value,
            "status": evaluation.status.value,
            "max_budget": business_goal.max_budget,
            "budget_remaining": evaluation.budget_remaining,
            "deadline_day": business_goal.deadline_day,
            "days_remaining": evaluation.days_remaining,
        }
















def create_business_run(
        random_seed: int=42,
) -> dict[str, Any]:
    """
    Creates one persistent simulation run

    Each autonomous operator attempt recieves it's own run id
    """

    with SessionLocal() as db:

        try:
            simulation_run = create_simulation_run(
                db,
                random_seed=random_seed,
            )
            db.commit()

            return {
                'run_id':simulation_run.id,
                "current_day": simulation_run.current_day,
                "total_spend": simulation_run.total_spend,
                "random_seed": simulation_run.random_seed,
                "status": simulation_run.status,
            }

        except Exception:
            db.rollback()
            raise
