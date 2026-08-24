"""
Run-scoped support-ticket analytics for the simulated SaaS business.

Every analytics function accepts a simulation run ID so support data
from one simulated business world is never mixed with another run.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import (
    Customer,
    SupportTicket,
)


def get_support_ticket_count(
    db: Session,
    run_id: int,
) -> int:
    """
    Return the total number of support tickets belonging to one
    simulation run.
    """

    statement = (
        select(
            func.count(SupportTicket.id)
        )
        .join(
            Customer,
            SupportTicket.customer_id == Customer.id,
        )
        .where(
            Customer.simulation_run_id == run_id
        )
    )

    count = db.scalar(statement)

    return count or 0


def get_ticket_count_by_category(
    db: Session,
    run_id: int,
) -> dict[str, int]:
    """
    Return support-ticket counts grouped by category for one
    simulation run.

    Example:

    {
        "billing": 2,
        "integration": 8,
        "login": 2,
    }
    """

    statement = (
        select(
            SupportTicket.category,
            func.count(SupportTicket.id),
        )
        .join(
            Customer,
            SupportTicket.customer_id == Customer.id,
        )
        .where(
            Customer.simulation_run_id == run_id
        )
        .group_by(
            SupportTicket.category
        )
        .order_by(
            SupportTicket.category
        )
    )

    rows = db.execute(statement).all()

    return {
        category: count
        for category, count in rows
    }


def get_customers_with_ticket_category(
    db: Session,
    run_id: int,
    category: str,
) -> int:
    """
    Return the number of unique customer companies in one simulation
    run that have at least one ticket in a particular category.
    """

    statement = (
        select(
            func.count(
                func.distinct(
                    SupportTicket.customer_id
                )
            )
        )
        .join(
            Customer,
            SupportTicket.customer_id == Customer.id,
        )
        .where(
            Customer.simulation_run_id == run_id,
            SupportTicket.category == category,
        )
    )

    count = db.scalar(statement)

    return count or 0


def get_ticket_categories_for_customer_status(
    db: Session,
    run_id: int,
    customer_status: str,
) -> dict[str, int]:
    """
    Return ticket counts grouped by category for customers with a
    particular status inside one simulation run.

    Example statuses:
    - trial
    - paid
    - churned
    """

    statement = (
        select(
            SupportTicket.category,
            func.count(SupportTicket.id),
        )
        .join(
            Customer,
            SupportTicket.customer_id == Customer.id,
        )
        .where(
            Customer.simulation_run_id == run_id,
            Customer.status == customer_status,
        )
        .group_by(
            SupportTicket.category
        )
        .order_by(
            SupportTicket.category
        )
    )

    rows = db.execute(statement).all()

    return {
        category: count
        for category, count in rows
    }


def get_support_summary(
    db: Session,
    run_id: int,
) -> dict:
    """
    Return the complete observable support summary for one simulation
    run.
    """

    return {
        "total_tickets": get_support_ticket_count(
            db,
            run_id,
        ),
        "all_categories": get_ticket_count_by_category(
            db,
            run_id,
        ),
        "trial_customer_categories":
            get_ticket_categories_for_customer_status(
                db,
                run_id,
                "trial",
            ),
        "paid_customer_categories":
            get_ticket_categories_for_customer_status(
                db,
                run_id,
                "paid",
            ),
    }