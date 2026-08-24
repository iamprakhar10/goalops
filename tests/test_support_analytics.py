"""
Tests for run-scoped support-ticket analytics.

Each test creates an independent SimulationRun and seeds its own
deterministic 20-company business world.
"""

from app.scripts.seed_demo_data import seed_business_world
from app.services.support_analytics import (
    get_customers_with_ticket_category,
    get_support_summary,
    get_support_ticket_count,
    get_ticket_count_by_category,
    get_ticket_categories_for_customer_status,
)
from app.simulation.run_store import create_simulation_run


def create_seeded_run(
    db_session,
):
    """
    Create one simulation run and seed its deterministic business world.
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


def test_support_ticket_count(
    db_session,
) -> None:
    """
    One baseline simulation run contains exactly 12 support tickets.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    count = get_support_ticket_count(
        db_session,
        simulation_run.id,
    )

    assert count == 12


def test_ticket_categories(
    db_session,
) -> None:
    """
    Verify the known support-ticket distribution for one run.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    categories = get_ticket_count_by_category(
        db_session,
        simulation_run.id,
    )

    assert categories == {
        "billing": 2,
        "integration": 8,
        "login": 2,
    }


def test_integration_ticket_customer_count(
    db_session,
) -> None:
    """
    Eight unique customer companies have integration problems.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    count = get_customers_with_ticket_category(
        db_session,
        simulation_run.id,
        "integration",
    )

    assert count == 8


def test_trial_customer_ticket_categories(
    db_session,
) -> None:
    """
    Trial companies contain the expected baseline support problems.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    categories = get_ticket_categories_for_customer_status(
        db_session,
        simulation_run.id,
        "trial",
    )

    assert categories == {
        "integration": 8,
        "login": 2,
    }


def test_support_summary(
    db_session,
) -> None:
    """
    Verify the complete support summary for one simulation run.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    summary = get_support_summary(
        db_session,
        simulation_run.id,
    )

    assert summary == {
        "total_tickets": 12,
        "all_categories": {
            "billing": 2,
            "integration": 8,
            "login": 2,
        },
        "trial_customer_categories": {
            "integration": 8,
            "login": 2,
        },
        "paid_customer_categories": {
            "billing": 2,
        },
    }


def test_support_analytics_are_isolated_between_runs(
    db_session,
) -> None:
    """
    Support analytics for one run must not include tickets belonging
    to another simulation run.
    """

    first_run = create_seeded_run(
        db_session,
    )

    second_run = create_seeded_run(
        db_session,
    )

    assert get_support_ticket_count(
        db_session,
        first_run.id,
    ) == 12

    assert get_support_ticket_count(
        db_session,
        second_run.id,
    ) == 12

    assert get_customers_with_ticket_category(
        db_session,
        first_run.id,
        "integration",
    ) == 8

    assert get_customers_with_ticket_category(
        db_session,
        second_run.id,
        "integration",
    ) == 8