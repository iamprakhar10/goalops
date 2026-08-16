"""
Support analytics services for teh simulated SaaS company

This module analyses support-ticket data to identify common 
customer problems and connect those problems with customer 
lifecycle states.

These functions will later provide evidence to our Autonomous busainess
operator when it will investigate why business metrics are underperforming
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Customer, SupportTicket












def get_support_ticket_count(
        db: Session,
) -> int:
    """
    Returns the total munber of support ticket
    """

    statement = select(
        func.count(SupportTicket.id)
    )

    count = db.scalar(statement)

    return count or 0











def get_ticket_count_by_category(
        db: Session,
) -> dict[str, int]:
    """
    Returns support-ticket counts grouped by category

    Eg.
        {
            "integration": 8,
            "billing": 2,
            "login": 2,
        }
    """

    statement = (
        select(
            SupportTicket.category,
            func.count(SupportTicket.id),
        )
        .group_by(
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
        category: str,
) -> int:
    """
    Returns the number of unique customer companies that have
    at least one support ticket in a particular category

    A company may open multiple support tickets, so distinct customer
    IDs prevent them from getting counted more than once
    """
    statement = (
        select(
            func.count(
                func.distinct(SupportTicket.customer_id)
            )
        )
        .where(
            SupportTicket.category == category
        )
    )

    count = db.scalar(statement)

    return count or 0








def get_ticket_categories_for_customer_status(
        db:Session,
        customer_status: str,
) -> dict[str, int]:
    """
    Returns support ticker categories for customer in a given
    lifecycle status

    Example:
        customer_status = 'trial'
    
    might return :
        {
            "integration": 8,
            "login": 2,
        }

    This will allow us to investigate which problems are especially
    common among trial, paid, or churned companies
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
            Customer.status == customer_status
        )
        .group_by(
            SupportTicket.category
        )
    )

    rows = db.execute(statement).all()

    return {
        category: count
        for category, count in rows
    }











def get_support_summary(
        db:Session,
) -> dict:
    """
    Retuerns a high-level summary of customer support problems

    Combine overall ticket counts with ticket category for trial
    and paid customer companies
    """

    return {
        "total_tickets": get_support_ticket_count(db),
        "all_categories": get_ticket_count_by_category(db),
        "trial_customer_categories": (
            get_ticket_categories_for_customer_status(
                db,
                "trial",
            )
        ),
        "paid_customer_categories": (
            get_ticket_categories_for_customer_status(
                db,
                "paid",
            )
        ),
    }