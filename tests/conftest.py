"""
Shared pytest fixtures for GoalOps tests.

This module provides reusable test dependencies such as a database
session.

Pytest automatically discovers fixtures defined in conftest.py.
"""

import pytest
from sqlalchemy.orm import Session

from app.database.db import SessionLocal


@pytest.fixture
def db_session() -> Session:
    """
    Provide a SQLAlchemy database session to a test.

    The session is rolled back after the test so temporary test data
    does not remain in the development database.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.rollback()
        db.close()