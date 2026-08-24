"""
Business Analytics services for our simulated SaaS company

This contains reusable functions for calculating business metrics
such as customer counts, onboarding funnel stages, and convertion rates

These are independent of FastAPI, MCP and the autonomous operator because 
we want to use them in many places
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import (
    Customer, 
    CustomerEvent,
    UserEvent,
    User,
)











def get_customer_count(
        db: Session,
        run_id: int,
) -> int:
    """
    Returns the total number of customer in the business
    """

    statement = (
        select(
            func.count(Customer.id)
        )
        .where(
            Customer.simulation_run_id == run_id
        )
    )


    count = db.scalar(statement)

    return count or 0
















def get_paid_customer_count(
        db: Session,
        run_id: int,
) -> int:
    """
    Returns the number of customer companies currently marked as paid
    """
    statement = (
        select(
            func.count(Customer.id)
        )
        .where(
            Customer.status == "paid",
            Customer.simulation_run_id == run_id,
        )
    )

    count = db.scalar(statement)

    return count or 0













def get_customers_with_lifecycle_event(
        db: Session,
        run_id: int,
        event_name: str,
) -> int:
    """
    Return the number of unique customer companies that reached
    a particular lifecycle milestone.

    Examples:
    - started_trial
    - started_onboarding
    - completed_onboarding
    - converted_to_paid

    Customer lifecycle events are normally expected to occur once
    per relevant company journey.

    DISTINCT customer IDs protect the metric from accidental duplicate
    event rows.
    """

    statement = (
        select(
            func.count(
                func.distinct(CustomerEvent.customer_id)
            )
        )
        .join(
            Customer,
            CustomerEvent.customer_id == Customer.id,
        )
        .where(
            Customer.simulation_run_id == run_id,
            CustomerEvent.event_name == event_name,
        )
    )
    count = db.scalar(statement)

    return count or 0















def get_user_event_count(
        db: Session,
        run_id: int,
        event_name: str,
) -> int:
    """
    Return the total number of times an employee-level action occurred.

    This counts event rows, not companies.

    Example:

    If employees across several companies ran workflows 25 times,
    this function returns 25.
    """

    statement = (
        select(
            func.count(UserEvent.id)
        )
        .join(
            User,
            UserEvent.user_id == User.id,
        )
        .join(
            Customer,
            User.customer_id == Customer.id,
        )
        .where(
            Customer.simulation_run_id == run_id,
            UserEvent.event_name == event_name,
        )
    )

    count = db.scalar(statement)

    return count or 0












def get_customers_with_user_event(
        db: Session,
        run_id: int,
        event_name: str,
) -> int:
    """
    Return the number of unique customer companies whose employees
    performed at least one particular user action inside the product.

    Example:

    Suppose:

        BrightDesk employee -> ran_workflow
        BrightDesk employee -> ran_workflow
        Nova employee       -> ran_workflow

    There are 3 UserEvent rows, but only 2 customer companies had
    employees who ran workflows.

    This function would therefore return 2.
    """
    statement = (
        select(
            func.count(
                func.distinct(User.customer_id)
            )
        )
        .join(
            UserEvent,
            UserEvent.user_id == User.id,
        )
        .join(
            Customer,
            User.customer_id == Customer.id,
        )
        .where(
            Customer.simulation_run_id == run_id,
            UserEvent.event_name == event_name,
        )
    )

    count = db.scalar(statement)

    return count or 0











def get_onboarding_funnel(
        db:Session,
        run_id: int,
) -> dict[str, int]:
    """
    Return the company-level onboarding and conversion funnel.

    Current funnel:

        started trial
            ↓
        started onboarding
            ↓
        completed onboarding
            ↓
        became paid

    Every number represents a count of unique customer companies,
    not individual employees or raw event rows.
    """

    started_trial = get_customers_with_lifecycle_event(
        db,
        run_id,
        "started_trial",
    )

    started_onboarding = get_customers_with_lifecycle_event(
        db,
        run_id,
        "started_onboarding",
    )

    completed_onboarding = get_customers_with_lifecycle_event(
        db,
        run_id,
        "completed_onboarding",
    )

    converted_to_paid = get_customers_with_lifecycle_event(
        db,
        run_id,
        "converted_to_paid",
    )

    return {
        "started_trial": started_trial,
        "started_onboarding": started_onboarding,
        "completed_onboarding": completed_onboarding,
        "converted_to_paid": converted_to_paid,
    }













def get_product_usage_summary(
        db:Session,
        run_id: int,

) -> dict[str, dict[str, int]]:
    """
    Returns a small summary of employee-level product usage

    Foe each important user action we calculate:
    - total_events:
        how many times the action happened

    - customer_companies:
        how many distinct customer companies had at least one
        employee perform that action

    Tis is important as employee actions may happen repeatedly 
    inside the same customer company.
    """
    event_names = [
        "logged_in",
        "connected_integration",
        "created_workflow",
        "ran_workflow",
    ]

    summary: dict[str, dict[str, int]] = {}

    for event_name in event_names:
        summary[event_name] = {
            "total_events": get_user_event_count(
                db,
                run_id,
                event_name,
            ),
            "customer_companies": get_customers_with_user_event(
                db,
                run_id,
                event_name,
            ),
        }

    return summary

















def get_conversion_rate(
    db: Session,
    run_id: int,
) -> float:
    """
    Return the percentage of customer companies currently marked as paid.

    Example:

        6 paid companies / 20 total companies
        = 30.0%

    Returns 0.0 when there are no customer companies.
    """

    total_customers = get_customer_count(
        db,
        run_id,
    )

    if total_customers == 0:
        return 0.0

    paid_customers = get_paid_customer_count(
        db,
        run_id,
    )

    conversion_rate = (
        paid_customers / total_customers
    ) * 100

    return round(
        conversion_rate,
        2,
    )