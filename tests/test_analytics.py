"""
Tests for run-scoped business analytics.

Every test creates its own SimulationRun and seeds a fresh deterministic
20-company business world.

This ensures analytics are calculated for one simulation run rather
than across all customer rows in the database.
"""

from app.scripts.seed_demo_data import seed_business_world
from app.services.analytics import (
    get_customer_count,
    get_customers_with_lifecycle_event,
    get_customers_with_user_event,
    get_onboarding_funnel,
    get_product_usage_summary,
    get_conversion_rate,
    get_user_event_count,
)
from app.simulation.run_store import create_simulation_run


def create_seeded_run(
    db_session,
):
    """
    Create one SimulationRun and seed its deterministic business world.

    Baseline world:
    - 20 customer companies
    - 6 paid companies
    - 14 companies started onboarding
    - 6 completed onboarding
    - 6 converted to paid
    """

    simulation_run = create_simulation_run(
        db_session,
        random_seed=42,
    )

    seed_business_world(
        db_session,
        simulation_run_id=simulation_run.id,
    )

    return simulation_run


def test_customer_count(
    db_session,
) -> None:
    """
    One seeded simulation run should contain exactly 20 companies.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    count = get_customer_count(
        db_session,
        simulation_run.id,
    )

    assert count == 20


def test_completed_onboarding_company_count(
    db_session,
) -> None:
    """
    Six baseline companies should have completed onboarding.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    count = get_customers_with_lifecycle_event(
        db_session,
        simulation_run.id,
        "completed_onboarding",
    )

    assert count == 6


def test_workflow_run_event_count(
    db_session,
) -> None:
    """
    The baseline world contains 12 ran_workflow event rows.

    Six activated companies each contribute two workflow-run events.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    count = get_user_event_count(
        db_session,
        simulation_run.id,
        "ran_workflow",
    )

    assert count == 12


def test_companies_that_ran_workflows(
    db_session,
) -> None:
    """
    Six unique companies have employees that ran workflows.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    count = get_customers_with_user_event(
        db_session,
        simulation_run.id,
        "ran_workflow",
    )

    assert count == 6


def test_onboarding_funnel(
    db_session,
) -> None:
    """
    The deterministic baseline funnel should match the seed data.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    funnel = get_onboarding_funnel(
        db_session,
        simulation_run.id,
    )

    assert funnel == {
        "started_trial": 20,
        "started_onboarding": 14,
        "completed_onboarding": 6,
        "converted_to_paid": 6,
    }


def test_product_usage_summary(
    db_session,
) -> None:
    """
    Product-usage analytics should match the deterministic seed data.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    summary = get_product_usage_summary(
        db_session,
        simulation_run.id,
    )

    assert summary == {
        "logged_in": {
            "total_events": 25,
            "customer_companies": 19,
        },
        "connected_integration": {
            "total_events": 14,
            "customer_companies": 14,
        },
        "created_workflow": {
            "total_events": 6,
            "customer_companies": 6,
        },
        "ran_workflow": {
            "total_events": 12,
            "customer_companies": 6,
        },
    }


def test_conversion_rate(
    db_session,
) -> None:
    """
    Six paid companies out of twenty gives a 30 percent conversion rate.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    conversion_rate = get_conversion_rate(
        db_session,
        simulation_run.id,
    )

    assert conversion_rate == 30.0


def test_analytics_are_isolated_between_runs(
    db_session,
) -> None:
    """
    Creating multiple runs must not cause analytics to combine them.

    Each run contains 20 companies and independently starts at
    30 percent conversion.
    """

    first_run = create_seeded_run(
        db_session,
    )

    second_run = create_seeded_run(
        db_session,
    )

    assert get_customer_count(
        db_session,
        first_run.id,
    ) == 20

    assert get_customer_count(
        db_session,
        second_run.id,
    ) == 20

    assert get_conversion_rate(
        db_session,
        first_run.id,
    ) == 30.0

    assert get_conversion_rate(
        db_session,
        second_run.id,
    ) == 30.0