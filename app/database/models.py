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

    support_tickets: Mapped[list[SupportTicket]] = relationship(
        back_populates="customer",
    )

    simulation_profile:  Mapped[CustomerSimulationProfile | None] = relationship(
        back_populates="customer",
        uselist=False,
    )

    simulation_run_id: Mapped[int|None] = mapped_column(
        ForeignKey('simulation_runs.id'),
        nullable=True,
    )

    simulation_run: Mapped[SimulationRun] = relationship(
        back_populates='customers',
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
    role:Mapped[str] = mapped_column(
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






















class SupportTicket(Base):
    """
    Represents a support request created by a customer company

    A ticket is attached to the customer company because it describes a
    problem that customer company is experiencing with our SaaS product

    Later we may also add the specific user who opened the ticket

    Examples:
    - integration setup problem
    - workflow creation confusion
    - billing question
    - login problem
    """

    __tablename__ = 'support_tickets'

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    customer: Mapped[Customer] = relationship(
        back_populates="support_tickets",
    )












# role







class CustomerSimulationProfile(Base):
    """
    Stores hidden simulaton traits for a customer company

    These values represnet characterstics of the fake company that
    influence how it behaves as simulated time advances.

    The autonomous operator will not directly see these hidden values
    It must infer likely causees from observable business data

    Values will be between 0 and 1

    intent_score:
        How strongly the customer company wants/needs thte product

    engagement_score:
        How likely employees are to actively use the product

    integration_difficulty:
        How difficult product integration is for this coustomer
        company
    """

    __tablename__ = "customer_simulation_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    customer_id : Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        unique=True,
        nullable=False,
    )

    intent_score: Mapped[float] = mapped_column(
        nullable=False,
    )

    engagement_score: Mapped[float] = mapped_column(
        nullable=False,
    )

    integration_difficulty: Mapped[float] = mapped_column(
        nullable=False,
    )

    customer: Mapped[Customer] = relationship(
        back_populates="simulation_profile"
    )




















class SimulationRun(Base):
    """
    Represents one independent simulated business run

    Each autonomous operator attempt gets its own SimulationRun

    The run stores simulation state that previously existed
    only in Python memory, allowing multiple runs to exist indpendently a
    and survive application restarts
    """

    __tablename__ = 'simulation_runs'

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    current_day: Mapped[int] = mapped_column(
        default=0,
    )

    total_spend: Mapped[float] = mapped_column(
        default=0.0,
    )

    random_seed: Mapped[int] = mapped_column()

    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    interventions: Mapped[
            list["SimulationRunIntervention"]
        ] = relationship(
            back_populates="simulation_run",
            cascade="all, delete-orphan",
        )

    customers: Mapped[list[Customer]] = relationship(
        back_populates="simulation_run",
        cascade="all, delete-orphan",
    )



"""
simulation_runs
       │
       │ 1
       │
       │ many
       ↓
simulation_run_interventions
"""




















class SimulationRunIntervention(Base):
    """
    Reperesents one intervention launched during a simulation run

    An intervention belongs to exactly one simulationRun and records
    when it started and when should the simulator evaluate it
    """

    __tablename__ = "simulation_run_interventions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    simulation_run_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_runs.id"),
    )

    intervention_name: Mapped[str] = mapped_column(
        String(100),
    )

    started_day: Mapped[int] = mapped_column()

    evaluation_day: Mapped[int] = mapped_column()

    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
    )

    simulation_run: Mapped["SimulationRun"] = relationship(
        back_populates="interventions",
    )