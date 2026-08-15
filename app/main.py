from fastapi import FastAPI 

# Creating a fastapi application
# Uvicorn will impoert this object when the server starts

app = FastAPI(
    title="GoalOps",
    description="Autonomous Business Goal Operator",
    version="0.1.0",
)

@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Checking whether the API server is running

    Later it can als be used by Docker, deployment platforms,
    monitoring systems or other services to verify that 
    GoalOps is alive
    """

    return {
        "status": "ok",
        "service": "goalops",
    }



