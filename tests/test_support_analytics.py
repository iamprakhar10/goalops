"""
Tests for support-ticket analytics.

These tests verify the intentionally encoded support patterns in the
deterministic SaaS demo dataset.

The known patterns will later let us evaluate whether the autonomous
operator correctly identifies customer problems from evidence.
"""

from app.database.db import SessionLocal
from app.services.support_analytics import (
    get_customers_with_ticket_category,
    get_support_summary,
    get_support_ticket_count,
    get_ticket_count_by_category,
    get_ticket_categories_for_customer_status,
)


def test_support_ticket_count() -> None:
    """
    The deterministic demo dataset contains 12 support tickets.
    """

    db = SessionLocal()

    try:
        assert get_support_ticket_count(db) == 12

    finally:
        db.close()


def test_ticket_categories() -> None:
    """
    Verify the known support-ticket distribution.
    """

    db = SessionLocal()

    try:
        categories = get_ticket_count_by_category(db)

        assert categories == {
            "billing": 2,
            "integration": 8,
            "login": 2,
        }

    finally:
        db.close()


def test_integration_ticket_customer_count() -> None:
    """
    Eight unique customer companies have integration support problems.
    """

    db = SessionLocal()

    try:
        count = get_customers_with_ticket_category(
            db,
            "integration",
        )

        assert count == 8

    finally:
        db.close()


def test_trial_customer_ticket_categories() -> None:
    """
    Trial companies primarily report integration problems in the
    deterministic demo scenario.
    """

    db = SessionLocal()

    try:
        categories = get_ticket_categories_for_customer_status(
            db,
            "trial",
        )

        assert categories == {
            "integration": 8,
            "login": 2,
        }

    finally:
        db.close()


def test_support_summary() -> None:
    """
    Verify the complete support analytics summary.
    """

    db = SessionLocal()

    try:
        summary = get_support_summary(db)

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

    finally:
        db.close()