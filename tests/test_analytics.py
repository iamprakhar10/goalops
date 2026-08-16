"""
Tests for the business analytics service.

These tests verify that analytics functions return the expected values
from the deterministic demo dataset.

Because the seed data is intentionally controlled, we know the correct
business metrics in advance and can use them to validate the analytics
layer.
"""

from app.database.db import SessionLocal
from app.services.analytics import (
    get_conversion_rate,
    get_customer_count,
    get_customers_with_lifecycle_event,
    get_customers_with_user_event,
    get_onboarding_funnel,
    get_product_usage_summary,
    get_user_event_count,
)


def test_customer_count() -> None:
    """
    The demo dataset contains exactly 20 customer companies.
    """

    db = SessionLocal()

    try:
        assert get_customer_count(db) == 20
    finally:
        db.close()


def test_completed_onboarding_company_count() -> None:
    """
    Six customer companies completed onboarding.
    """

    db = SessionLocal()

    try:
        count = get_customers_with_lifecycle_event(
            db,
            "completed_onboarding",
        )

        assert count == 6
    finally:
        db.close()


def test_workflow_run_event_count() -> None:
    """
    Employee users generated 12 ran_workflow events in total.
    """

    db = SessionLocal()

    try:
        count = get_user_event_count(
            db,
            "ran_workflow",
        )

        assert count == 12
    finally:
        db.close()


def test_companies_that_ran_workflows() -> None:
    """
    The 12 workflow-run events belong to only 6 customer companies.
    """

    db = SessionLocal()

    try:
        count = get_customers_with_user_event(
            db,
            "ran_workflow",
        )

        assert count == 6
    finally:
        db.close()


def test_onboarding_funnel() -> None:
    """
    Verify the known customer-company onboarding funnel.
    """

    db = SessionLocal()

    try:
        funnel = get_onboarding_funnel(db)

        assert funnel == {
            "started_trial": 20,
            "started_onboarding": 14,
            "completed_onboarding": 6,
            "converted_to_paid": 6,
        }
    finally:
        db.close()


def test_product_usage_summary() -> None:
    """
    Verify employee-level product usage aggregated by company.
    """

    db = SessionLocal()

    try:
        summary = get_product_usage_summary(db)

        assert summary == {
            "logged_in": {
                "total_events": 26,
                "customer_companies": 20,
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
    finally:
        db.close()


def test_conversion_rate() -> None:
    """
    Six of twenty customer companies are paid.

    6 / 20 = 30%.
    """

    db = SessionLocal()

    try:
        assert get_conversion_rate(db) == 30.0
    finally:
        db.close()