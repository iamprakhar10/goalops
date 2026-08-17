"""
Simulation state for the fake SaaS business environment

This module stores information about the simulated world that is
not part of an y individual customere record, such as current simulated day and which business 
interventions are currently active.

The autonomous operator will eventually inspect the business, choose
interventions, and ask the simulation engine to advance time
"""


from dataclasses import dataclass, field
from app.simulation.interventions import ActiveIntervention

@dataclass
class SimulationState:
    """
    Represents current global state of one simulation run

    current_day:
        Number of simulated days passed till now

    active_interventions:
        Business interventions that have been activated and are currently
        affecting future customer behavior in the simulation.
    """

    current_day: int = 0

    active_interventions: dict[
        str,
        ActiveIntervention,
    ] = field(
        default_factory=dict,
    )

    total_spend: float = 0.0

    random_seed: int = 42