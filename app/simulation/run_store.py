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










def save_simulation_state(
        db: Session,
        run_id: int,
        state: SimulationState,
) -> None:
    """
    Perssist the current SimulationState

    This stores
    - current simulated day
    - intervention spending
    - random seed
    - active interventions

    Interventions that were previously active but are no longer in the 
    SimulationState are marked completed

    The function flushes but does not commit
    """

    simulation_run = get_simulation_run(
        db,
        run_id=run_id,
    )

    if simulation_run is None:
        raise ValueError(
            f"Simulation run {run_id} does not exist"
        )

    # ---------------------------------------------------------
    # SAVE BASIC SIMULATION STATE
    # ---------------------------------------------------------

    simulation_run.current_day = state.current_day
    simulation_run.total_spend = state.total_spend
    simulation_run.random_seed = state.random_seed

    # ---------------------------------------------------------
    # LOAD CURRENTLY ACTIVE STORED INTERVENTIONS
    # ---------------------------------------------------------

    statement = (
        select(SimulationRunIntervention)
        .where(
            SimulationRunIntervention.simulation_run_id
            ==run_id,
            SimulationRunIntervention.status
            =='active',
        )
    )

    stored_active_rows = list(
        db.scalars(statement)
    )

    stored_by_name = {
        row.intervention_name: row
        for row in stored_active_rows
    }

    # ---------------------------------------------------------
    # MARK FINISHED INTERVENTIONS AS COMPLETED
    # ---------------------------------------------------------

    for intervention_name, row in stored_by_name.items():
        if (
            intervention_name
            not in state.active_interventions
        ):
            row.status = 'completed'

    # ---------------------------------------------------------
    # STORE NEWLY ACTIVE INTERVENTIONS
    # ---------------------------------------------------------
    for (
        intervention_name,
        active_intervention
    ) in state.active_interventions.items():

        if intervention_name in stored_by_name:
            continue

        row = SimulationRunIntervention(
            simulation_run_id=run_id,
            intervention_name=intervention_name,
            started_day=active_intervention.started_day,
            evaluation_day=active_intervention.evaluation_day,
            status='active',
        )

        db.add(row)

    db.flush()













def update_simulation_run_status(
        db: Session,
        run_id: int,
        status: str,
) -> None:
    """
    Update the lifecycle status of one persisitent run

    Expected statuses include:

    - active
    - achieved
    - failed

    This function flushes but does not commit so the caller controls
    the transaction boundary
    """

    simulation_run = get_simulation_run(
        db=db,
        run_id=run_id,
    )
    if simulation_run is None:
        raise ValueError(
            f"Simulation run {run_id} does not exist"
        )

    simulation_run.status = status

    db.flush()