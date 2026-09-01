# GoalOps — Autonomous Business Goal Operator

GoalOps is an autonomous-agent system that operates a simulated B2B SaaS business toward a measurable business goal.

The current objective is to increase **trial-to-paid conversion to at least 40%**, subject to a **$2,000 intervention budget** and a **30-day simulated deadline**.

## Core loop

```text
Observe business
      ↓
LLM decides
      ↓
Use MCP tool
      ↓
Simulation advances
      ↓
Observe new state
      ↓
Repeat until goal achieved/failed
```

The project deliberately separates three responsibilities:

- **Operator:** decides what action to take.
- **Simulation:** determines what happens after an action.
- **Evaluator:** objectively determines whether the goal was achieved.

This prevents the LLM from directly controlling the business or grading itself.

## Why MCP?

MCP provides a controlled boundary between the LLM and the business environment.

The operator does not directly modify the database. It interacts through exposed tools such as:

```text
business_snapshot
available_interventions
run_intervention
advance_time
goal_status
```

The current implementation uses MCP **in-process**, so there is no separate Uvicorn/MCP server that needs to be started before running the operator.

## Why a simulation?

A real business environment is difficult to experiment on safely and reproducibly.

The simulator provides:

- a known starting state,
- constrained interventions,
- delayed consequences,
- stochastic outcomes,
- budget and time limits,
- reproducible random seeds.

The seeded business contains different customer situations, giving the operator a problem to investigate rather than a hard-coded action.

## Important engineering decisions

### Separate decisions from consequences

The LLM chooses interventions; the simulation determines their effects.

**Problem solved:** the agent cannot directly manipulate or guarantee the outcome.

### Simulated time

Interventions can have delayed effects without waiting in real time.

```text
run intervention
      ↓
advance simulated time
      ↓
evaluation day reached
      ↓
simulation applies outcome
```

### Persistent simulation runs

A simulation run represents one independent business world and is stored in PostgreSQL.

**Problem solved:** runs can be inspected and resumed instead of existing only in memory.

### Persistent operator activity

Operator sessions and tool calls are stored separately from business state.

**Problem solved:** agent behavior becomes auditable and evaluable.

### Objective evaluation

The application independently checks the goal instead of trusting the LLM's final response.

```text
in_progress
achieved
failed
```

**Problem solved:** the agent cannot declare its own success.

### Random seeds

The simulation contains stochastic outcomes while seeds make runs reproducible.

**Problem solved:** the operator can be benchmarked across controlled runs.

## Evaluation and benchmarking

The benchmark evaluates multiple independent simulation runs.

It measures both:

**Business outcome**
- goal success/failure
- final metric
- spending
- simulated days
- interventions used

**Operator behavior**
- tool calls
- business inspection
- inspection before intervention
- operator sessions/resumes
- termination reasons

Execution errors are tracked separately from legitimate business failures.

For example:

```text
execution_status = "completed"
goal_status      = "failed"
```

means the operator executed normally but did not achieve the business goal.

## Benchmark result

A 10-seed benchmark produced:

```text
Runs:                       10
Successful runs:             9
Execution errors:            1
Success rate:               90.0%

Average final metric:       46.11%
Average spend:            $1,266.67
Average days used:           7.78
Average tool calls:          6.78

Inspected business:         100%
Inspected before action:    100%
```

These results describe performance **inside the simulated environment** and are not evidence of real-world business impact.

## Limitations

- Intervention effects are predefined by the simulator.
- Customer behavior is modeled rather than learned from real businesses.
- The current implementation focuses on trial-to-paid conversion.
- The benchmark is relatively small.
- There is no proper no-intervention causal control yet.
- LLM/API failures can cause execution errors.

## Running the project

### Requirements

- Python 3.14+
- PostgreSQL
- Groq API access

### 1. Configure environment

Create `.env`:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
GROQ_API_KEY=<your-api-key>
GROQ_MODEL=<optional-model-name>
```

Do not commit `.env` or API keys.

### 2. Install dependencies

Install the dependencies defined in `pyproject.toml`.

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Seed the simulation

```bash
python -m app.scripts.seed_demo_data
```

### 5. Run the autonomous operator

```bash
python -m app.scripts.run_tool_operator
```

### 6. Resume a simulation run

```bash
python -m app.scripts.resume_tool_operator
```

Update the run ID in the script when necessary.

### 7. Run the benchmark

```bash
python -m app.scripts.run_benchmark
```

### 8. Run tests

```bash
pytest -q
```

## Project status

The core system is complete:

- Simulation environment
- Persistent simulation runs
- MCP integration
- LLM tool calling
- Autonomous operator loop
- Session/resume support
- Tool-call persistence
- Objective evaluation
- Multi-seed benchmarking
- Automated tests

The next stage is deeper evaluation and presentation rather than adding more core infrastructure.
