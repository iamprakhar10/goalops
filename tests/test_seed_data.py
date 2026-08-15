from sqlalchemy import func, select

from app.database.db import SessionLocal
from app.database.models import Customer


def test_database_contains_seed_customers() -> None:
    """
    Verify that demo seed data exists.

    This is a simple integration-style test against the local
    development database.
    """

    db = SessionLocal()

    try:
        statement = select(func.count(Customer.id))
        customer_count = db.scalar(statement)

        assert customer_count == 20

    finally:
        db.close()