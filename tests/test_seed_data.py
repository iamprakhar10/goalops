"""
Tests for simulation-run-scoped seed data.

Seed data now belongs to individual SimulationRun records, so tests
must count rows belonging to a particular run rather than counting
the entire database.
"""

from sqlalchemy import func, select

from app.database.models import Customer, User
from app.scripts.seed_demo_data import seed_business_world
from app.simulation.run_store import create_simulation_run


def create_seeded_run(
    db_session,
):
    """
    Create one simulation run with its deterministic business world.
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


def test_database_contains_seed_customers(
    db_session,
) -> None:
    """
    One seeded simulation run should contain exactly 20 customers.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    statement = (
        select(
            func.count(Customer.id)
        )
        .where(
            Customer.simulation_run_id
            == simulation_run.id
        )
    )

    customer_count = (
        db_session.scalar(statement)
        or 0
    )

    assert customer_count == 20


def test_database_contains_seed_users(
    db_session,
) -> None:
    """
    One seeded simulation run should contain exactly 26 employees.
    """

    simulation_run = create_seeded_run(
        db_session,
    )

    statement = (
        select(
            func.count(User.id)
        )
        .join(
            Customer,
            User.customer_id == Customer.id,
        )
        .where(
            Customer.simulation_run_id
            == simulation_run.id
        )
    )

    user_count = (
        db_session.scalar(statement)
        or 0
    )

    assert user_count == 26


def test_two_runs_have_separate_customer_rows(
    db_session,
) -> None:
    """
    Two simulation runs should each receive their own 20 customer rows.
    """

    first_run = create_seeded_run(
        db_session,
    )

    second_run = create_seeded_run(
        db_session,
    )

    first_count = db_session.scalar(
        select(
            func.count(Customer.id)
        )
        .where(
            Customer.simulation_run_id
            == first_run.id
        )
    )

    second_count = db_session.scalar(
        select(
            func.count(Customer.id)
        )
        .where(
            Customer.simulation_run_id
            == second_run.id
        )
    )

    assert first_count == 20
    assert second_count == 20
    assert first_run.id != second_run.id