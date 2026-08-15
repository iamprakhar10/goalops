import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL is not configured.")

# Engine -> SQLAlchemy's connection interface to our PostgreSQL
# database
engine = create_engine(DATABASE_URL)


# SessionLocal is a factory for database sessions
# In the project we will use these sessions 
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models in GoalOps.
    """

    pass