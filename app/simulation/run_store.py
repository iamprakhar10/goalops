"""
Persistence helpers for goalops simulation runs

This module stores and reconstructs SimulationState objects using postgreSQL

The simulator itself can continue working with the existing SimulationState
dataclass, while this module handles converting that temporatry python
representation to and from persistent database rows
"""


from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import (
    SimulationRun,
    SimulationRunIntervention,
)
from app.simulation.interventions import ActiveIntervention
from app.simulation.state import SimulationState




def create_simulation_run(
        db: Session,
        random_seed: int,
) -> SimulationRun:
    """
    Create one new independent simulation run

    A newly created ru always start at:

    day 0
    zero intervention spending
    no active interventions
    """

    simulation_run = SimulationRun(
        current_day=0,
        total_spend=0.0,
        random_seed=random_seed,
        status="active",
    )

    db.add(
        simulation_run
    )

    db.flush()
    db.refresh(simulation_run)

    return simulation_run







def get_simulation_run(
        db: Session,
        run_id: int,
) -> SimulationRun|None:
    """
    Retrieve one simulation run by it's database ID
    """

    statement = (
        select(SimulationRun)
        .where(
            SimulationRun.id == run_id
        )
    )

    return db.scalar(
        statement
    )









def load_simulation_state(
        db: Session,
        run_id: int,
) -> SimulationState:
    """
    Recostruct the in-memory SimulationState for a stored run

    Active interventions are loaded from the database and converted
    back into AvtiveIntervention dataclass object
    """

    simulation_run = get_simulation_run(
        db,
        run_id=run_id,
    )

    if simulation_run is None:
        raise ValueError(
            f"Simulation run {run_id} does not exist"
        )

    statement = (
        select(SimulationRunIntervention)
        .where(
            SimulationRunIntervention.simulation_run_id
            ==run_id,
            SimulationRunIntervention.status
            == 'active',
        )
    )

    intervention_rows = list(db.scalars(statement))

    active_interventions = {
        row.intervention_name: ActiveIntervention(
            name=row.intervention_name,
            started_day=row.started_day,
            evaluation_day=row.evaluation_day,
        )
        for row in intervention_rows
    }

    return SimulationState(
        current_day=simulation_run.current_day,
        active_interventions=active_interventions,
        total_spend=simulation_run.total_spend,
        random_seed=simulation_run.random_seed,
    )