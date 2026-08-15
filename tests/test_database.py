from sqlalchemy import text

from app.database.db import engine


def test_database_connection() -> None:
    """
    Verify that GoalOps can connect to PostgreSQL
    and execute a simple SQL query.
    """

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )

        assert result.scalar() == 1