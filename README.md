# Queue Maintenance AI Agent

A highly scalable LangGraph AI agent developed to safely manage execution actions by leveraging progressive autonomy, structual Human-in-the-loop limits, and event-sourcing undo action logic.

## Overview
Developed in response to recent high-profile "vibe coding" errors (like the Replit database wipe), this project proves that safe AI agent logic resides purely in architectural guardrails – not prompt advisory guidelines.

## Features
- **LangGraph Integration**: Stateful multi-actor orchestration pipeline.
- **Progressive Trust Actions**: Tracks action-level successful executions securely via database counters.
- **Human-In-The-Loop**: Forces high-risk unproven operations to halt dynamically until manually reviewed.
- **Event-Sourcing Safety Net**: Perfect snapshot JSON serialization occurs prior to mutation guaranteeing reversible data deletions.
- **Observability**: Supports full node execution trees and LLM inputs via LangSmith tracing.

## Setup Instructions

### Local Environment
1. Initialize virtual environment: `python -m venv .venv`
2. Activate: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux)
3. Install reqs: `pip install -r requirements.txt`
4. Copy `.env.example` -> `.env` and fill values (LangSmith).

### Docker setup
1. Build application: `docker-compose up --build -d`
2. Run database verifications: `docker-compose exec app pytest tests/`
3. Observe tests output successfully inside the Docker application.

## Core Executions
- `python src/cli.py --inspect` -> View the local execution content queue.
- `python src/cli.py --query "Publish item post_001"` -> Send instruction to Agent state machine.
- `python src/cli.py --resume Y` -> Approve pending action interrupt.

### Adversarial Testing
Run `python tests/simulate_failure.py` to deploy an intentional destruction query and verify the underlying LangGraph framework correctly isolates and rolls back the failure mode.
