# Sentinel-V: Autonomous DevOps Agent System

## Project Overview

Sentinel-V is an autonomous DevOps research project demonstrating how AI coding agents can monitor, triage, and patch bugs in a production-like application — without human intervention. The sentinel agent system observes a running app, detects anomalies, diagnoses root causes, and applies fixes autonomously.

## Repository Structure

```
sentinel/          ← autonomous agent system (active development focus)
toy_app/           ← deliberately buggy e-commerce FastAPI app (demo target)
```

## toy_app — DO NOT FIX BUGS

**The bugs in `toy_app/` are intentional. Do not fix them.**

The toy_app is a demo target for the sentinel agents to discover and patch autonomously. It contains 4 known intentional bugs:

1. **Memory Leaker** — global cache accumulates without eviction, causing unbounded memory growth
2. **LIKE Search Bug** — product search uses `LIKE` on a non-indexed column, causing full table scans
3. **In-Memory Filtering Bug** — fetches all products from DB and filters in Python instead of at the query level
4. **Third-Party Service Flake** — payment service failures are not handled gracefully (no retry/fallback)

These bugs exist so that the sentinel agents can find and fix them as part of the demo. If you touch toy_app code, only do so to support the sentinel system's ability to interact with it (e.g., adding observability hooks), never to fix the bugs directly.

## sentinel — Active Development

The `sentinel/` directory contains the autonomous agent system. This is where development work should be focused. Key agents:

- **Orchestrator** — coordinates the overall bug-detection and fix cycle
- **Router** — dispatches tasks to the appropriate specialist agents
- **Sentry** — monitors metrics and detects anomalies
- **Mechanic** — diagnoses root causes and generates patches
- **Auditor** — reviews and validates proposed fixes before application

See `sentinel/CLAUDE.md` for detailed agent guidelines and conventions.

## Stack

| Component | Technologies |
|-----------|-------------|
| toy_app   | FastAPI, PostgreSQL, Prometheus, Grafana, Docker |
| sentinel  | pydantic-ai, asyncio, MCP, Claude models (claude-sonnet-4-6 / claude-opus-4-6) |
