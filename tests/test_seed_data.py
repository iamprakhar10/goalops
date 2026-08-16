"""
Tests for the deterministic SaaS demo dataset.

These tests verify that the local demo seed contains the expected number
of customer companies and users. The known dataset gives later analytics
tests a stable foundation.
"""

from sqlalchemy import func, select

from app.database.db import SessionLocal
from app.database.models import Customer, User


def test_database_contains_seed_customers() -> None:
    """
    Verify that the demo dataset contains exactly 20 customer companies.
    """

    db = SessionLocal()

    try:
        statement = select(
            func.count(Customer.id)
        )

        customer_count = db.scalar(statement)

        assert customer_count == 20

    finally:
        db.close()


def test_database_contains_seed_users() -> None:
    """
    Verify that the 20 demo companies contain 26 employee users.
    """

    db = SessionLocal()

    try:
        statement = select(
            func.count(User.id)
        )

        user_count = db.scalar(statement)

        assert user_count == 26

    finally:
        db.close()