"""
Business intevention definitions for our SaaS simulation

This module defines the actions that our Autonomous operator is allowed to 
take inside the simualated company

The AI/LLM wil eventually choose among these interventions, but it cannot 
invent arbitrary database changes. We will be predefining every possible 
interventions, these interventions will have predefined costs, duration,
targetting rules, and effects on customer behaviour

The simulation engine remains responsible for determiningthe actual 
business outcome
"""


from dataclasses import dataclass



@dataclass(frozen=True)
class InterventionDefinition:
    """
    Defines a single buseness intervention available in our simulator

    name:
        stable programmatic name of the intervention

    description:
        Human readable explanation of the business action

    cost:
        Simulated monetary cost of launching this intervention

    duration_days:
        Number of simulated days before it's outcome is evealuated
    
    onboarding_bonus:
        Increase in onboarding-completion probability

    convertion_bonus:
        Increase in paid-conversoin probability

    target_ticket_category:
        Optional support ticket category used to target companies
        If this is None, it means that interventin can target trial 
        companies generally rather than customer companies with
        one particular issue
    """

    name: str
    description: str

    cost: float
    duration_days: int

    onboarding_bonus: float = 0.0
    conversion_bonus: float = 0.0

    target_ticket_category: str | None = None












@dataclass
class ActiveIntervention:
    """
    Represents an intervention that has actually been launched

    started_day:
        Simulated day on which the intervention began

    evaluation_day:
        Day on which the simulatpor evaluates it's outcome.
    """

    name: str
    started_day: int
    evaluation_day: int
















GUIDED_INTEGRATION_HELP = "guided_integration_help"

ONBOARDING_EMAIL = "onboarding_email"

WORKFLOW_TEMPLATE = "workflow_template"


INTERVENTION_REGISTRY: dict[
    str,
    InterventionDefinition,
] = {
    GUIDED_INTEGRATION_HELP: InterventionDefinition(
        name=GUIDED_INTEGRATION_HELP,
        description=(
            "Provide guided setup assistance to trial companies "
            "experiencing integration problems."
        ),
        cost=1200.0,
        duration_days=7,
        onboarding_bonus=0.45,
        conversion_bonus=0.0,
        target_ticket_category="integration",
    ),

    ONBOARDING_EMAIL: InterventionDefinition(
        name=ONBOARDING_EMAIL,
        description=(
            "Send additional onboarding guidance to trial companies "
            "that have started onboarding."
        ),
        cost=300.0,
        duration_days=7,
        onboarding_bonus=0.15,
        conversion_bonus=0.0,
        target_ticket_category=None,
    ),

    WORKFLOW_TEMPLATE: InterventionDefinition(
        name=WORKFLOW_TEMPLATE,
        description=(
            "Provide ready-made workflow templates to help trial "
            "companies reach product activation faster."
        ),
        cost=800.0,
        duration_days=7,
        onboarding_bonus=0.25,
        conversion_bonus=0.10,
        target_ticket_category=None,
    ),
}












def get_intervention(
        name: str,
) -> InterventionDefinition:
    """
    Return an intervention definition by name.

    Raise ValueError if the requested intervention does not exist.
    """

    intervention = INTERVENTION_REGISTRY.get(name)

    if intervention is None:
        raise ValueError(
            f"Unknown intervention: {name}"
        )

    return intervention