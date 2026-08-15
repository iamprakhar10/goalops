from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base








class Customer(Base):
    """
    Represents a customer account in our simulated Business
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    company_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    segment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="trial",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )