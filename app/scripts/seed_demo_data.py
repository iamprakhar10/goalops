from datetime import datetime, timedelta, timezone

from app.database.db import SessionLocal
from app.database.models import Customer, ProductEvent, Subscription


def add_event(
    customer_id: int,
    event_name: str,
    occurred_at: datetime,
) -> ProductEvent:
    """
    Create one product event for a customer.

    This helper keeps the seed function easier to read.
    """

    return ProductEvent(
        customer_id=customer_id,
        event_name=event_name,
        occurred_at=occurred_at,
    )


def seed_demo_data() -> None:
    """
    Insert a small deterministic SaaS dataset.

    This is intentionally NOT random.

    We want known patterns in the data so we can later verify
    that analytics queries and the autonomous operator are able
    to discover those patterns correctly.
    """

    db = SessionLocal()

    try:
        # Prevent accidental duplicate seeding.
        existing_customer = db.query(Customer).first()

        if existing_customer is not None:
            print("Database already contains customers. Seed skipped.")
            return

        now = datetime.now(timezone.utc)

        customers: list[Customer] = []

        # ---------------------------------------------------------
        # Group 1:
        # Customers who complete onboarding and convert to paid.
        # ---------------------------------------------------------
        for i in range(1, 7):
            customer = Customer(
                company_name=f"Activated Company {i}",
                segment="smb",
                status="paid",
            )

            db.add(customer)
            db.flush()

            db.add(
                Subscription(
                    customer_id=customer.id,
                    plan="starter",
                    status="active",
                    started_at=now - timedelta(days=20 - i),
                    ended_at=None,
                )
            )

            db.add_all(
                [
                    add_event(
                        customer.id,
                        "signed_up",
                        now - timedelta(days=20 - i),
                    ),
                    add_event(
                        customer.id,
                        "started_onboarding",
                        now - timedelta(days=19 - i),
                    ),
                    add_event(
                        customer.id,
                        "imported_data",
                        now - timedelta(days=18 - i),
                    ),
                    add_event(
                        customer.id,
                        "completed_onboarding",
                        now - timedelta(days=17 - i),
                    ),
                ]
            )

            customers.append(customer)

        # ---------------------------------------------------------
        # Group 2:
        # Trial customers who started onboarding but did not finish.
        # ---------------------------------------------------------
        for i in range(1, 9):
            customer = Customer(
                company_name=f"Stalled Company {i}",
                segment="smb",
                status="trial",
            )

            db.add(customer)
            db.flush()

            db.add(
                Subscription(
                    customer_id=customer.id,
                    plan="trial",
                    status="active",
                    started_at=now - timedelta(days=10 - i),
                    ended_at=None,
                )
            )

            db.add_all(
                [
                    add_event(
                        customer.id,
                        "signed_up",
                        now - timedelta(days=10 - i),
                    ),
                    add_event(
                        customer.id,
                        "started_onboarding",
                        now - timedelta(days=9 - i),
                    ),
                ]
            )

            customers.append(customer)

        # ---------------------------------------------------------
        # Group 3:
        # Trial customers who never even started onboarding.
        # ---------------------------------------------------------
        for i in range(1, 7):
            customer = Customer(
                company_name=f"Inactive Company {i}",
                segment="smb",
                status="trial",
            )

            db.add(customer)
            db.flush()

            db.add(
                Subscription(
                    customer_id=customer.id,
                    plan="trial",
                    status="active",
                    started_at=now - timedelta(days=5 - i),
                    ended_at=None,
                )
            )

            db.add(
                add_event(
                    customer.id,
                    "signed_up",
                    now - timedelta(days=5 - i),
                )
            )

            customers.append(customer)

        db.commit()

        print(f"Seeded {len(customers)} customers.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()