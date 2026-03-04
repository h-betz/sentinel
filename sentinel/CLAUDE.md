# Sentinel Agent Package

## Purpose
Sentinel is a standalone, embeddable autonomous agent package. It monitors a target
application, detects failures, routes problems to the appropriate AI model, and
dispatches repair agents to implement fixes. It is designed to be integrated into
other applications as a self-contained sub-package.

## Tech Stack
- **pydantic-ai** for agent orchestration and tool registration
- **asyncio** for async execution throughout
- **subprocess** for running tests as part of repair verification

## Code Style

### Imports
- All imports must be at the **top of the file** — never inside functions or methods
- Use **explicit imports only** — no wildcard imports (`from module import *`)
- Group imports: stdlib → third-party → local, separated by blank lines

```python
# Good
import asyncio
import os
import subprocess
from dataclasses import dataclass
from typing import Dict

from pydantic_ai import Agent, RunContext
```

### Agent Structure
Each agent follows a consistent pattern:
1. A `@dataclass` for deps (named `<AgentName>Deps`)
2. A class with `Agent` instantiated in `__init__` with explicit `model` and `deps_type`
3. A `_register_tools()` private method called from `__init__` to attach tools
4. A public `async def run(...)` method that constructs deps and invokes `self.agent.run()`

### Type Hints
- Full type annotations on all functions and methods
- Use `Dict`, `List`, etc. from `typing` for consistency with existing agent files
- Return types always annotated

### Async
- All agent tools must be `async def`
- All public `run()` methods must be `async def`
- Use `await asyncio.sleep()` — never `time.sleep()`

### Docstrings
- Module-level docstring on every file (brief, single purpose)
- Short docstring on each tool describing what it does and why

## Project Structure
```
sentinel/
├── orchestrator.py      # Main loop: detect → route → repair
├── router.py            # Rule-based model selection by error type
└── agents/
    ├── sentry.py        # Monitoring agent: detects anomalies via Prometheus
    ├── mechanic.py      # Repair agent: reads, patches, and tests code fixes
    └── auditor.py       # Verification agent (stub)
```

## Adding New Agents
1. Create `sentinel/agents/<name>.py` with module docstring
2. Define `<Name>Deps` dataclass
3. Implement the class with `__init__`, `_register_tools()`, and `async def run()`
4. Import and invoke from `orchestrator.py`
