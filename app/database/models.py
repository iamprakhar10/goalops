from __future__ import annotations
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

    # Broad company category used for business analysis.
    #
    # Examples:
    # - smb
    # - midmarket
    # - enterprise
    segment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Current high-level state of the customer company.
    #
    # Examples:
    # - trial
    # - paid
    # - churned
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
    subscriptions: Mapped[list[Subscription]] = relationship(
        back_populates='customer',
    )

    # Company-level lifecycle milestones.
    customer_events: Mapped[list[CustomerEvent]] = relationship(
        back_populates="customer",
    )

    # Employees/users belonging to this customer company.
    users: Mapped[list[User]] = relationship(
        back_populates="customer",
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

     # Commercial plan associated with this subscription.
    #
    # Examples:
    # - trial
    # - starter
    # - pro
    # - enterprise
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # State of this particular subscription record.
    #
    # Examples:
    # - active
    # - converted
    # - expired
    # - cancelled
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

    customer: Mapped[Customer] = relationship(
        back_populates='subscriptions',
    )



















class CustomerEvent(Base):
    """
    Represents a company-level lifecycle event or milestone.

    These events describe changes in the customer company's journey
    with our SaaS product.

    They are not individual button clicks performed by employees.

    Examples:
    - started_trial
    - started_onboarding
    - completed_onboarding
    - converted_to_paid
    - churned

    For milestone events such as completed_onboarding, we normally
    expect one occurrence for a particular customer journey.
    """

    __tablename__ = "customer_events"

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

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Customer company associated with this lifecycle event.
    customer: Mapped[Customer] = relationship(
        back_populates="customer_events",
    )





















class User(Base):
    """
    Represents an individual employee inside a customer company
    Example:

        Customer:
            BrightDesk

        Users:
            Arjun - Sales Manager
            Riya  - Support Manager
            Kabir - Operations Manager
    """

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # Job/function of the employee inside the customer company.
    #
    # Examples:
    # - sales_manager
    # - support_manager
    # - operations_manager
    # - admin
    role:Mapped[int] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable= False,
    )

    # Company this employee belongs to.
    customer: Mapped[Customer] = relationship(
        back_populates="users",
    )

    # Product actions performed by this employee.
    user_events: Mapped[list[UserEvent]] = relationship(
        back_populates="user",
    )





















class UserEvent(Base):
    """
    Represents a product action performed by an individual employee
    of customer company


    These are different from CustomerEvent records.

    CustomerEvent:
        describes the company's lifecycle.

    UserEvent:
        describes what a human user did inside the product.

    Examples:
    - logged_in
    - created_workflow
    - ran_workflow
    - connected_integration
    - invited_user

    These events may naturally happen many times.

    """

    __tablename__ = 'user_events'

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    event_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Employee who performed this product action.
    user: Mapped[User] = relationship(
        back_populates='user_events'
    )



















