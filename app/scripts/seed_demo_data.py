"""
Seed a small deterministic dataset for the simulated SaaS company.

This script creates a controlled set of customer companies, subscriptions,
company-level lifecycle events, employees, and employee-level product events.

The dataset is intentionally deterministic rather than random. This allows
us to know the underlying business pattern in advance and later verify
whether our analytics and autonomous operator discover it correctly.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.database.models import (
    Customer,
    CustomerEvent,
    Subscription,
    User,
    UserEvent,
    SupportTicket,
    CustomerSimulationProfile,
)
from app.simulation.run_store import create_simulation_run

def create_customer_event(
    customer_id: int,
    event_name: str,
    occurred_at: datetime,
) -> CustomerEvent:
    """
    Create a company-level lifecycle event.

    Examples:
    - started_trial
    - started_onboarding
    - completed_onboarding
    - converted_to_paid
    """

    return CustomerEvent(
        customer_id=customer_id,
        event_name=event_name,
        occurred_at=occurred_at,
    )


def create_user_event(
    user_id: int,
    event_name: str,
    occurred_at: datetime,
) -> UserEvent:
    """
    Create an employee-level product usage event.

    Examples:
    - logged_in
    - connected_integration
    - created_workflow
    - ran_workflow
    """

    return UserEvent(
        user_id=user_id,
        event_name=event_name,
        occurred_at=occurred_at,
    )


def clear_demo_data() -> None:
    """
    Remove existing demo business data.

    Child tables are deleted before parent tables because of foreign-key
    relationships.

    This makes the seed script repeatable during development.
    """

    db = SessionLocal()

    try:
        db.execute(delete(UserEvent))
        db.execute(delete(SupportTicket))
        db.execute(delete(User))
        db.execute(delete(CustomerEvent))
        db.execute(delete(Subscription))
        db.execute(delete(CustomerSimulationProfile))
        db.execute(delete(Customer))

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def seed_business_world(
        db: Session,
        simulation_run_id: int,
) -> None:
    """
    Insert 20 deterministic customer companies.

    The companies are divided into three groups:

    Group 1:
        6 activated companies.
        They completed onboarding and became paid customers.

    Group 2:
        8 stalled trial companies.
        They started onboarding but never completed it.

    Group 3:
        6 inactive trial companies.
        They started a trial but barely used the product.

    This creates a known relationship between product activation
    and paid conversion that we can analyze later.
    """
    now = datetime.now(timezone.utc)
    
    # ---------------------------------------------------------
    # GROUP 1
    #
    # 6 companies successfully activate and become paid.
    # ---------------------------------------------------------

    for i in range(1, 7):

        customer = Customer(
            company_name=f"Activated Company {i}",
            segment="smb",
            status="paid",
            simulation_run_id=simulation_run_id,
        )

        db.add(customer)

        # flush() sends the INSERT to PostgreSQL without committing.
        #
        # We need this so PostgreSQL gives the Customer an ID before
        # we create related subscriptions, users, and events.
        db.flush()

        trial_started_at = now - timedelta(days=30 - i)

        db.add(
            Subscription(
                customer_id=customer.id,
                plan="starter",
                status="active",
                started_at=trial_started_at,
                ended_at=None,
            )
        )
        db.add(
            CustomerSimulationProfile(
                customer_id=customer.id,
                intent_score=0.85,
                engagement_score=0.80,
                integration_difficulty=0.20,
            )
        )

        # Company-level lifecycle milestones.
        db.add_all(
            [
                create_customer_event(
                    customer.id,
                    "started_trial",
                    trial_started_at,
                ),
                create_customer_event(
                    customer.id,
                    "started_onboarding",
                    trial_started_at + timedelta(days=1),
                ),
                create_customer_event(
                    customer.id,
                    "completed_onboarding",
                    trial_started_at + timedelta(days=3),
                ),
                create_customer_event(
                    customer.id,
                    "converted_to_paid",
                    trial_started_at + timedelta(days=7),
                ),
            ]
        )

        # Each company gets two employees using the product.
        admin_user = User(
            customer_id=customer.id,
            name=f"Activated Admin {i}",
            role="admin",
        )

        operations_user = User(
            customer_id=customer.id,
            name=f"Activated Operations {i}",
            role="operations_manager",
        )

        db.add_all(
            [
                admin_user,
                operations_user,
            ]
        )

        db.flush()

        # Employee-level product actions.
        db.add_all(
            [
                create_user_event(
                    admin_user.id,
                    "logged_in",
                    trial_started_at,
                ),
                create_user_event(
                    admin_user.id,
                    "connected_integration",
                    trial_started_at + timedelta(days=1),
                ),
                create_user_event(
                    admin_user.id,
                    "created_workflow",
                    trial_started_at + timedelta(days=2),
                ),
                create_user_event(
                    admin_user.id,
                    "ran_workflow",
                    trial_started_at + timedelta(days=3),
                ),
                create_user_event(
                    operations_user.id,
                    "logged_in",
                    trial_started_at + timedelta(days=2),
                ),
                create_user_event(
                    operations_user.id,
                    "ran_workflow",
                    trial_started_at + timedelta(days=4),
                ),
            ]
        )
        if i <= 2:
            db.add(
                SupportTicket(
                    customer_id=customer.id,
                    category="billing",
                    subject="Question about plan billing",
                    description=(
                        "We completed setup successfully but have a "
                        "question about our subscription billing."
                    ),
                    status="resolved",
                    created_at=trial_started_at + timedelta(days=8),
                )
            )

    # ---------------------------------------------------------
    # GROUP 2
    #
    # 8 companies start onboarding but get stuck.
    # ---------------------------------------------------------

    for i in range(1, 9):

        customer = Customer(
            company_name=f"Stalled Company {i}",
            segment="smb",
            status="trial",
            simulation_run_id=simulation_run_id,
        )

        db.add(customer)
        db.flush()

        trial_started_at = now - timedelta(days=20 - i)

        db.add(
            Subscription(
                customer_id=customer.id,
                plan="trial",
                status="active",
                started_at=trial_started_at,
                ended_at=None,
            )
        )


        db.add(
            CustomerSimulationProfile(
                customer_id=customer.id,
                intent_score=0.65,
                engagement_score=0.45,
                integration_difficulty=0.85,
            )
        )

        db.add_all(
            [
                create_customer_event(
                    customer.id,
                    "started_trial",
                    trial_started_at,
                ),
                create_customer_event(
                    customer.id,
                    "started_onboarding",
                    trial_started_at + timedelta(days=1),
                ),
            ]
        )

        user = User(
            customer_id=customer.id,
            name=f"Stalled Admin {i}",
            role="admin",
        )

        db.add(user)
        db.flush()

        db.add_all(
            [
                create_user_event(
                    user.id,
                    "logged_in",
                    trial_started_at,
                ),
                create_user_event(
                    user.id,
                    "connected_integration",
                    trial_started_at + timedelta(days=1),
                ),
            ]
        )
        # These stalled companies are intentionally given support
        # problems related to integration setup.
        #
        # This creates a known hidden pattern:
        #
        # integration friction
        #       ↓
        # onboarding stalls
        #
        # Later our autonomous operator should discover this from
        # the data rather than being told directly.
        db.add(
            SupportTicket(
                customer_id=customer.id,
                category="integration",
                subject="Integration setup problem",
                description=(
                    "We are having trouble connecting our integration "
                    "and cannot continue setting up the product."
                ),
                status="open",
                created_at=trial_started_at + timedelta(days=2),
            )
        )

    # ---------------------------------------------------------
    # GROUP 3
    #
    # 6 companies start trials but hardly use the product.
    # ---------------------------------------------------------

    for i in range(1, 7):

        customer = Customer(
            company_name=f"Inactive Company {i}",
            segment="smb",
            status="trial",
            simulation_run_id=simulation_run_id,
        )

        db.add(customer)
        db.flush()

        trial_started_at = now - timedelta(days=10 - i)

        db.add(
            Subscription(
                customer_id=customer.id,
                plan="trial",
                status="active",
                started_at=trial_started_at,
                ended_at=None,
            )
        )

        db.add(
            create_customer_event(
                customer.id,
                "started_trial",
                trial_started_at,
            )
        )



        db.add(
            CustomerSimulationProfile(
                customer_id=customer.id,
                intent_score=0.20,
                engagement_score=0.15,
                integration_difficulty=0.35,
            )
        )

        user = User(
            customer_id=customer.id,
            name=f"Inactive Admin {i}",
            role="admin",
        )

        db.add(user)
        db.flush()

        # They logged in once and then effectively disappeared.
        db.add(
            create_user_event(
                user.id,
                "logged_in",
                trial_started_at,
            )
        )

        if i <= 2:
            db.add(
                SupportTicket(
                    customer_id=customer.id,
                    category="login",
                    subject="Trouble signing in",
                    description=(
                        "One of our employees is having trouble "
                        "signing in to the product."
                    ),
                    status="open",
                    created_at=trial_started_at + timedelta(days=1),
                )
            )

    #     db.commit()

    #     print("Seeded 20 customer companies.")

    # except Exception:
    #     db.rollback()
    #     raise

    # finally:
    #     db.close()



def clear_simulation_run_data(
    db: Session,
    simulation_run_id: int,
) -> None:
    """
    Delete only the business data belonging to one simulation run.

    Child rows are deleted before Customer rows so foreign-key
    constraints are respected.

    Data belonging to other simulation runs is left untouched.

    UserEvent
    ↓
    SupportTicket
    CustomerEvent
    Subscription
    CustomerSimulationProfile
    ↓
    User
    ↓
    Customer
    """

    customer_ids = (
        select(Customer.id)
        .where(
            Customer.simulation_run_id
            == simulation_run_id
        )
    )

    user_ids = (
        select(User.id)
        .where(
            User.customer_id.in_(
                customer_ids
            )
        )
    )

    # User events depend on users.
    db.execute(
        delete(UserEvent)
        .where(
            UserEvent.user_id.in_(
                user_ids
            )
        )
    )

    # These tables depend directly on Customer.
    db.execute(
        delete(SupportTicket)
        .where(
            SupportTicket.customer_id.in_(
                customer_ids
            )
        )
    )

    db.execute(
        delete(CustomerEvent)
        .where(
            CustomerEvent.customer_id.in_(
                customer_ids
            )
        )
    )

    db.execute(
        delete(Subscription)
        .where(
            Subscription.customer_id.in_(
                customer_ids
            )
        )
    )

    db.execute(
        delete(CustomerSimulationProfile)
        .where(
            CustomerSimulationProfile.customer_id.in_(
                customer_ids
            )
        )
    )

    # Users can now be deleted because their UserEvents are gone.
    db.execute(
        delete(User)
        .where(
            User.customer_id.in_(
                customer_ids
            )
        )
    )

    # Finally delete the customers belonging only to this run.
    db.execute(
        delete(Customer)
        .where(
            Customer.simulation_run_id
            == simulation_run_id
        )
    )

    db.flush()





def seed_demo_data() -> None:
    """
    Manual development entry point.

    Creates one new SimulationRun and seeds a fresh 20-company
    business world belonging only to that run.
    """

    db = SessionLocal()

    try:
        simulation_run = create_simulation_run(
            db,
            random_seed=42,
        )

        seed_business_world(
            db,
            simulation_run_id=simulation_run.id,
        )

        db.commit()

        print(
            f"Seeded 20 customer companies "
            f"for simulation run {simulation_run.id}."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()




if __name__ == "__main__":
    
    seed_demo_data()