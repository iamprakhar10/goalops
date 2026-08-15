from fastapi.testclient import TestClient

from app.main import app


# TestClient behaves like an HTTP client talking to our
# FastAPI application, without requiring us to manually
# start Uvicorn during the test.
client = TestClient(app)


def test_health_check() -> None:
    """
    The health endpoint should confirm that GoalOps is running.
    """

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "service": "goalops",
    }