# FLOW

A visual, extensible workflow/application builder. Compose triggers, logic, data/API integrations, and AI nodes into executable workflows on a canvas.

LiveDemo: https://flow-three-pi.vercel.app/workflows <br>
Repository: https://github.com/CoderKanha47/FLOW

## Stack

- **Backend** — Python 3.12, FastAPI, SQLAlchemy, SQLite (dev) / PostgreSQL (Docker)
- **Engine** — sandboxed expression evaluator (`{{...}}` interpolation), async executor
- **Frontend** — Next.js 15 (App Router), React 19, Tailwind CSS v4, React Flow (@xyflow/react v12)

## Quick start (local dev)

### 1. Backend

```powershell
cd E:\flow\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env    # adjust defaults if needed
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API docs: http://localhost:8000/docs · Health: http://localhost:8000/health

### 2. Frontend

```powershell
cd E:\flow\frontend
npm install
copy .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                          # http://localhost:3000
```

### 3. Run the tests

```powershell
cd E:\flow\backend
.\.venv\Scripts\python.exe -m pytest tests\ -q
```

## Docker

```powershell
cd E:\flow
docker compose up --build
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000 · Postgres: localhost:5432

## Node catalog

| Type              | Category      | Purpose                                        |
| ----------------- | ------------- | ---------------------------------------------- |
| `manual_trigger`  | Trigger       | Run from the "Run" button in the editor        |
| `schedule_trigger`| Trigger       | Cron/interval scheduling (MVP: spec only)      |
| `webhook`         | Trigger       | Inbound HTTP trigger with secret + publishing  |
| `transform`       | Logic         | Expression/Jinja-style transforms              |
| `condition`       | Logic         | If/else branching on a boolean expression      |
| `http_request`    | Integration   | Outbound HTTP with `{{...}}` templates         |
| `database`        | Integration   | Parameterized DB ops (no arbitrary SQL)        |
| `llm`             | AI            | OpenAI / Groq / Ollama / Anthropic providers   |
| `log`             | Utility       | Logs data at a point in the workflow           |

## Expression language

Values from upstream nodes are interpolated with `{{nodeName.path.to.value}}`.
Additional namespaces: `trigger` (trigger payload), `input` (manual run inputs),
and `variables` (user-defined variables set in the Run panel — store API keys here).

- Built-in: arithmetic, comparisons, `and` / `or` / `not`, dict/list/tuple literals, and attribute/map access.
- Evaluation is a safe AST evaluator — Python `eval` is never used; no code-execution node is provided.

## Architecture notes

- **Execution engine** is the core: it rebuilds a validated `Graph` from persisted nodes/edges and runs it with the async `Executor`. Validation catches missing triggers, multiple triggers, cycles, unknown nodes/edges, and unreachable merges before anything executes.
- **Branching**: condition nodes declare `decides_branch`; edges carry a `branch` (`true` / `false`). A node is ready when *at least one* active incoming predecessor has executed (never-taken branches don't block merges).
- **Security**: own-workflow-only access enforced at the service layer; secrets stored as encrypted blobs (Fernet, key from `SECRET_ENCRYPTION_KEY`); DB interactions are parameterized only; no user code runs in the main process.
- **Node registry is extensible**: implement `BaseNode` and register via `app/nodes` (`registry.py`); UI config panels are generated from the `/api/workflows/node-types` metadata endpoint.

## Project layout

```
backend/
  app/
    api/routes/        # auth, workflows, executions, webhooks
    engine/            # executor, graph, expressions, context
    models/            # SQLAlchemy models
    nodes/             # node implementations + registry
    services/          # workflow & execution services
  tests/               # pytest suite (engine + API)
frontend/
  app/                 # Next.js App Router pages
  components/          # editor, canvas, palette, run/history panels
  lib/                 # API client, types, RF<=>backend converters
docker-compose.yml
```

## MVP scope (deliberate omissions)

- No background scheduler/cron daemon yet — `schedule_trigger` is spec-only.
- No realtime WebSocket execution streaming (executions are stored + fetched).
- No Redis/Kafka/k8s; single-process engine is the MVP architecture.
