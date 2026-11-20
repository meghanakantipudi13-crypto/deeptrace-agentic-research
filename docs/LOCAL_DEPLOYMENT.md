# Local Deployment

DeepTrace's submission deployment is a local FastAPI service. This topology is intentional: the capstone permits a justified alternative deployment, and the graders assess the recorded system behavior rather than a public URL. It demonstrates the complete agent graph without provisioning recurring cloud infrastructure.

## Components

- FastAPI/Jinja application at `http://127.0.0.1:8000`
- LangGraph workflow with SQLite checkpoints
- bounded filesystem JSON research history
- deterministic planning and a development-only correction demo provider

The SQLite and filesystem stores survive a process restart on the same machine. They are not distributed, multi-user, or cloud-durable storage.

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,production]"
```

## Run the recorded-demo configuration

```powershell
.\scripts\run_demo.ps1
```

Open <http://127.0.0.1:8000>. This mode is clearly marked simulated and makes no paid or external search calls. It deterministically demonstrates approval, a quarantined retrieval instruction, an evidence gap, query revision, a second retrieval pass, cited synthesis, and persisted history.

## Optional live Vertex planning

Vertex planning uses Application Default Credentials and environment configuration; credentials are never committed. The controlled Phase 8 smoke test used project `csci599-deeptrace-510206`, location `global`, and model `gemini-3.5-flash-lite`. Live Tavily retrieval was not verified and is not needed for the submission demonstration.

## Persistence check

1. Complete an approved research run.
2. Confirm it appears in **Research History**.
3. Stop the server and run `scripts/run_demo.ps1` again.
4. Confirm the completed run still appears.

## Limitations

This deployment has no authentication, shared database, distributed lock, shared rate limiter, or public TLS endpoint. PostgreSQL, GCS, Tavily, and Cloud Run adapters remain implementation/future integration work and are not claimed as live-verified capabilities.
