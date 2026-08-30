# GoalOps — Autonomous Business Goal Operator

GoalOps is an experimental autonomous-agent system that operates a **simulated B2B SaaS business** toward a measurable business goal.

Instead of giving an LLM direct access to a database or allowing it to directly modify business outcomes, GoalOps separates the system into three parts:

1. **Agent** — decides what action to take.
2. **Simulation environment** — executes approved actions and determines their business consequences.
3. **Evaluator** — objectively measures what happened.

The operator interacts with the simulated business through **MCP (Model Context Protocol) tools**.

The current benchmark goal is:

> **Increase trial-to-paid conversion to at least 40% within 30 simulated days and within a $2,000 intervention budget.**

---

## Why this project?

A simple LLM application can generate recommendations, but that is different from an autonomous system that must:

- observe a changing environment,
- choose actions,
- execute those actions through tools,
- wait for delayed consequences,
- observe the resulting state,
- respect budget and deadline constraints,
- decide whether to continue or stop,
- and be evaluated independently of its own claims.

GoalOps was built to explore that complete loop in a controlled environment.

The simulated environment makes experiments reproducible while keeping the consequences of actions under programmatic control.

---

## Architecture

```text
                         ┌──────────────────────┐
                         │   Business Goal       │
                         │                      │
                         │ 40% conversion       │
                         │ 30-day deadline      │
                         │ $2,000 max budget    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Autonomous LLM     │
                         │      Operator        │
                         │                      │
                         │ Observe → Decide     │
                         │ → Act → Observe      │
                         └──────────┬───────────┘
                                    │
                              MCP tools
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    MCP Server        │
                         │                      │
                         │ business_snapshot   │
                         │ available_interventions
                         │ run_intervention     │
                         │ advance_time         │
                         │ goal_status          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │     Simulation Environment   │
                    │                              │
                    │ Customers                    │
                    │ Events                       │
                    │ Support tickets              │
                    │ Hidden customer traits        │
                    │ Intervention effects          │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                         ┌──────────────────────┐
                         │ PostgreSQL           │
                         │                      │
                         │ Runs                 │
                         │ Customers            │
                         │ Events               │
                         │ Interventions        │
                         │ Operator sessions    │
                         │ Tool calls            │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Deterministic        │
                         │ Evaluation            │
                         │                      │
                         │ Goal result          │
                         │ Cost                 │
                         │ Time                 │
                         │ Actions              │
                         │ Inspection behavior  │
                         └──────────────────────┘
```

### Core separation

The central design rule is:

```text
Agent:
    decides what to do

Environment:
    determines what actually happens

Evaluator:
    determines how the run performed
```

The LLM cannot directly update customer records or declare the business goal achieved.

---

## How an operator run works

A typical MCP-native run follows this loop:

```text
Create SimulationRun
        │
        ▼
Check objective goal status
        │
        ▼
LLM receives observable business state
        │
        ▼
LLM requests MCP tool call(s)
        │
        ▼
Application executes the tool through MCP
        │
        ▼
Tool result is persisted
        │
        ▼
Result is returned to the LLM
        │
        ▼
LLM decides what to do next
        │
        ├── inspect business
        ├── inspect interventions
        ├── launch intervention
        ├── advance simulated time
        └── check goal
        │
        ▼
Goal achieved / failed / execution limit
```

When an intervention is launched, it does **not** immediately force a successful outcome.

For example:

```text
launch intervention
        ↓
intervention becomes active
        ↓
simulation time advances
        ↓
intervention reaches evaluation day
        ↓
simulation engine evaluates affected customers
        ↓
business state changes according to
predefined probabilities + customer traits + randomness
```

This keeps the LLM responsible for **decision-making**, while the simulator remains responsible for **causal consequences inside the model**.

---

## The simulated business

The seed script creates a deterministic 20-company business world with three broad groups:

- **6 activated companies** — already completed onboarding and became paid.
- **8 stalled trial companies** — started onboarding but are stuck, with integration-related support problems.
- **6 inactive trial companies** — started trials but have very little product usage.

The customer data includes:

- company segment and status,
- subscriptions,
- company lifecycle events,
- employees,
- employee-level product events,
- support tickets,
- hidden simulation profiles.

### Observable vs hidden information

The operator can observe business evidence such as:

- conversion rate,
- onboarding funnel,
- product usage,
- support-ticket summaries,
- current simulated day,
- spending,
- intervention history.

The simulator also stores hidden customer traits:

- `intent_score`
- `engagement_score`
- `integration_difficulty`

These hidden traits influence simulation outcomes but are deliberately not exposed to the operator.

The operator therefore has to reason from observable business evidence rather than receiving the simulator's underlying causal parameters directly.

---

## Interventions

The current intervention registry contains three predefined actions:

| Intervention | Cost | Duration | Main effect |
|---|---:|---:|---|
| `guided_integration_help` | $1,200 | 7 days | Helps trial companies with integration problems |
| `onboarding_email` | $300 | 7 days | Additional onboarding guidance |
| `workflow_template` | $800 | 7 days | Helps trial companies reach activation faster |

The LLM cannot invent arbitrary interventions.

It receives the available intervention definitions through MCP and can only request approved actions.

The simulation engine determines the eventual outcome.

---

## MCP architecture

GoalOps uses MCP as the boundary between the autonomous operator and the business environment.

The MCP server exposes:

```text
business_snapshot
create_run
available_interventions
run_intervention
advance_time
goal_status
```

The operator discovers the available MCP tools and converts their definitions into the format required by the Groq tool-calling API.

Conceptually:

```text
                    LLM
                     │
              tool request
                     │
                     ▼
              MCP client
                     │
                     ▼
              MCP server
                     │
                     ▼
          application tool layer
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     analytics             simulation
          │                     │
          └──────────┬──────────┘
                     ▼
                 PostgreSQL
```

This means the operator does not need direct access to:

- SQLAlchemy sessions,
- database tables,
- analytics implementation,
- simulation internals.

MCP provides the tool interface through which the agent interacts with the environment.

---

## Persistence and simulation runs

A `SimulationRun` represents one independent simulated business world.

It stores persistent simulation-level state such as:

- run ID,
- current simulated day,
- total intervention spend,
- random seed,
- lifecycle status.

`SimulationState` is the Python representation used by the simulation engine:

- current simulated day,
- active interventions,
- total spend,
- random seed.

The persistence layer converts between the in-memory `SimulationState` and database-backed `SimulationRun` / intervention records.

This separation allows the simulation engine to work with a simple state object while allowing runs to survive process boundaries and application restarts.

### Operator sessions

A simulation run can contain multiple `OperatorSession` records.

This allows an operator run to be stopped and later resumed without creating a new business world.

Each session records its own termination reason and completion time.

### Tool-call history

Every MCP tool call made by the operator is persisted in `OperatorToolCall`.

This provides a reconstructable record of what the operator actually did across sessions.

---

## Goal definition and evaluation

Goals are explicitly represented by `BusinessGoal`:

```text
metric_name
target_value
deadline_day
max_budget
```

The current benchmark goal is:

```text
metric_name  = trial_to_paid_conversion
target_value = 40.0
deadline_day = 30
max_budget   = 2000.0
```

`GoalStatus` has three states:

```text
in_progress
achieved
failed
```

`GoalEvaluation` is the deterministic result of evaluating the current goal state.

The goal evaluator checks:

1. whether spending exceeded the budget,
2. whether the target metric has been reached,
3. whether the deadline has passed,
4. otherwise, whether the goal remains in progress.

The evaluator does not ask the LLM whether it succeeded.

For example, the LLM may say:

```text
"Goal achieved."
```

but the application independently calls `goal_status` and evaluates the actual simulated business state.

---

## Run-level evaluation

`SimulationRunEvaluation` summarizes a complete simulation run.

It records:

- goal status,
- final metric,
- target value,
- total spend,
- simulated days used,
- number of recorded operator tool calls,
- interventions launched,
- whether the business was inspected,
- whether inspection happened before the first intervention,
- number of operator sessions,
- number of resumes,
- termination history.

This makes evaluation based on persisted system state rather than on the LLM's self-report.

---

## Benchmarking

The benchmark runs the operator independently across multiple random seeds.

Each seed creates a new isolated `SimulationRun`.

`BenchmarkRunResult` represents one seed's result.

`BenchmarkResult` aggregates the benchmark:

- total runs,
- successful runs,
- failed runs,
- in-progress runs,
- execution errors,
- success rate,
- average final metric,
- average spend,
- average days used,
- average tool calls,
- business-inspection rate,
- inspection-before-action rate,
- average operator sessions,
- average resumes,
- termination counts,
- intervention counts,
- individual run results.

Importantly:

```text
execution_status = "completed"
```

means the benchmark/operator execution completed without a technical exception.

It does **not** mean that the business goal was achieved.

Business success is represented separately by:

```text
evaluation.goal_status
```

This distinction allows a legitimate business failure to remain different from an infrastructure/runtime failure.

---

## Example benchmark

A 10-seed benchmark produced the following aggregate result during development:

```text
Total runs:                    10
Successful business runs:      9
Execution errors:              1
Success rate:                  90.0%

Average final metric:          46.11%
Average spend:                 $1,266.67
Average days used:             7.78
Average tool calls:            6.78

Business inspected:            100%
Inspected before action:       100%

Average operator sessions:      1.0
Average resumes:               0.0
```

The benchmark also showed different strategies across seeds. For example, some successful runs reached the target with only `onboarding_email`, while others used both `guided_integration_help` and `onboarding_email`.

A separate seed-5 run demonstrated a legitimate business failure:

```text
final conversion: 35%
target:            40%
spend:             $2,000
simulated day:     30
status:            failed
```

This is useful because the simulator is not designed to guarantee that the operator always succeeds.

### What the benchmark does and does not prove

The current benchmark demonstrates autonomous goal pursuit and measurable operational behavior **inside this simulation**.

It does **not** establish causal business lift relative to a no-intervention control condition.

That is an important limitation of the current evaluation methodology.

---


```

### Package responsibilities

**`app/database/`**

SQLAlchemy database configuration and ORM models.

**`app/goals/`**

Business-goal definitions and deterministic goal evaluation.

**`app/mcp/`**

The MCP boundary: server-exposed tools, their application-layer implementations, and the MCP client wrapper.

**`app/operator/`**

The autonomous decision-making system, including LLM integration, prompts, tool calling, sessions, evaluation, and benchmarking.

**`app/services/`**

Reusable business analytics independent of the LLM and MCP layers.

**`app/simulation/`**

The simulated business world, intervention definitions, time advancement, intervention effects, and persistent simulation-state handling.

**`app/scripts/`**

Command-line entry points for seeding, running, resuming, testing, and benchmarking the system.

---

## Database model

The main database entities are:

```text
SimulationRun
    │
    ├── Customers
    │      ├── Users
    │      ├── CustomerEvents
    │      ├── UserEvents
    │      ├── SupportTickets
    │      └── CustomerSimulationProfile
    │
    ├── SimulationRunIntervention
    │
    └── OperatorSession
             │
             └── OperatorToolCall
```

### Why both customer and user events?

The simulation distinguishes:

**CustomerEvent**

Company-level lifecycle milestones:

```text
started_trial
started_onboarding
completed_onboarding
converted_to_paid
churned
```

**UserEvent**

Individual employee product actions:

```text
logged_in
connected_integration
created_workflow
ran_workflow
```

This allows the business analytics layer to reason about both company lifecycle and employee product usage.

---

## Reproducibility

Simulation runs use a `random_seed`.

The simulation engine combines the run's seed with intervention evaluation timing when creating its random generator.

This allows benchmark runs to be reproduced for the same seed while still producing stochastic customer outcomes.

---

## Setup

### Requirements

The project currently declares:

- Python `>=3.14`
- PostgreSQL
- Groq API access

Python dependencies are declared in `pyproject.toml`.

### Environment variables

Create a `.env` file containing:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
GROQ_API_KEY=<your-groq-api-key>
GROQ_MODEL=<optional-model-name>
```

`GROQ_MODEL` defaults in the current implementation to:

```text
openai/gpt-oss-20b
```

Do not commit `.env` or API keys to the repository.

### Database migrations

After configuring the database:

```bash
alembic upgrade head
```

---

## Seed the simulation data

The demo seeding script creates the deterministic business world used by the simulation.

The script is designed to clear previous demo business data before reseeding it.

Use:

```bash
python -m app.scripts.seed_demo_data
```

---

## Run the operator

The MCP-native operator can be started with:

```bash
python -m app.scripts.run_tool_operator
```

The script creates a new simulation run, executes the autonomous operator, and prints an objective evaluation.

---

## Resume an existing run

The project supports resuming an existing persistent simulation run.

The resume entry point is:

```bash
python -m app.scripts.resume_tool_operator
```

The current development script contains a specific example run ID; update that value before using it for a different persisted run.

---

## Run the benchmark

The benchmark entry point runs seeds `1` through `10` in the current implementation:

```bash
python -m app.scripts.run_benchmark
```

It prints structured JSON containing both aggregate metrics and per-run results.

---

## Run tests

Run the test suite with:

```bash
pytest -q
```

---

## Design principles

### 1. The LLM does not control business outcomes

The LLM selects actions.

The simulator determines their consequences.

### 2. Goal completion is deterministic

The LLM cannot declare success.

Application code evaluates the actual business state.

### 3. The agent receives observable evidence

Hidden simulation traits are not exposed to the operator.

### 4. Actions are constrained

The operator can only use the tools and interventions exposed by the application.

### 5. Simulation state is persistent

A run can survive beyond one operator session.

### 6. Operator behavior is observable

MCP calls are persisted so the run can be evaluated after execution.

### 7. Evaluation is separated from decision-making

The system does not rely on the agent to grade itself.

### 8. Reproducibility matters

Random seeds allow controlled benchmark experiments.

---

## What kinds of problems can GoalOps solve?

The architecture is intentionally broader than the current conversion-rate example.

The general problem class is:

> **Given a measurable business objective, an observable business environment, a constrained set of actions, resource limits, and delayed consequences, autonomously choose and sequence actions until the objective is achieved or the constraints make further pursuit impossible.**

The current implementation demonstrates this with:

```text
trial-to-paid conversion
```

The same architecture could eventually support goals such as:

```text
increase activation
reduce churn
increase product adoption
reduce support backlog
improve onboarding completion
increase workflow usage
```

Those are **future extensions**, not metrics currently implemented by the goal evaluator.

---

## Current limitations

GoalOps is deliberately a simulated environment, so its results should not be interpreted as evidence of real-world business performance.

Current limitations include:

- only one goal metric is currently supported by the goal evaluator,
- intervention effects are predefined simulation rules,
- the current benchmark does not provide a no-intervention causal control,
- the benchmark is relatively small,
- LLM/provider reliability can affect execution,
- the simulation's hidden causal structure is hand-designed,
- the current operator's action space is intentionally constrained.

These limitations are part of the experimental design and provide clear directions for future work.

---

## Future directions

Possible extensions include:

- additional business metrics and goals,
- stronger causal/counterfactual evaluation,
- larger benchmark suites,
- more diverse simulated business environments,
- improved intervention selection,
- richer long-horizon planning,
- more sophisticated failure recovery,
- independent evaluation models,
- benchmark result visualization,
- stronger robustness analysis across seeds and environments.

---

## Project status

The core autonomous business operator is implemented, including:

```text
Simulation environment       ✅
Persistent simulation runs  ✅
MCP server/client            ✅
LLM tool calling             ✅
Autonomous operator loop     ✅
Operator sessions/resume    ✅
Tool-call persistence        ✅
Deterministic evaluation     ✅
Multi-seed benchmark         ✅
Automated tests              ✅
```

The project is now primarily at the stage of **final documentation, analysis, and presentation**, rather than core-system construction.
