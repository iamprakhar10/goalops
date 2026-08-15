from datetime import datetime

from sqlalchemy import DateTime, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    # One customer may have subscription records over time 
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates='customer',
    )

    #  One customer may generate many product events
    product_events: Mapped[list['ProductEvent']] = relationship(
        back_populates='customer',
    )













class Subscription(Base):
    """
    Represents a customer's subsciption 

    Example
    - Free trial
    - Paid starter plan
    - paid pro plan
    - cancelled subscription
    """

    __tablename__   = "subscriptions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey('customers.id'),
        nullable= False,
    )

    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer: Mapped["Customer"] = relationship(
        back_populates='subscriptions',
    )





















class ProductEvent(Base):
    """
    Represents something a customer did inside a SaaS product
    
    Examples:
    - Signed_up
    - Logged_in
    - Started_onboarding
    - imported_data
    - completed_onboarding
    - used_automation
    """
    __tablename__ = "product_events"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    event_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    occured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    customer: Mapped['Customer'] = relationship(
        back_populates='product_events',
    )














