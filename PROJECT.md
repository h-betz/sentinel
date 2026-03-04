# Sentinel-V: The Cost-Resilient Self-Healing API
**A Portfolio Project for the 2026 AI-Native Engineering Era**

## 1. Project Overview
Sentinel-V is an autonomous "Level 4" DevOps system. It doesn't just monitor applications; it understands them. It uses a multi-agent mesh to detect failures, architect fixes, and audit code for security—all while utilizing **Semantic Routing** to ensure AI compute costs remain sustainable.



## 2. Core Features
* **Autonomous Triage:** Uses local, low-cost LLMs (Llama 3.1) for 24/7 observability.
* **Semantic Cost Router:** Automatically selects the most cost-effective model (Tier 1, 2, or 3) based on task complexity.
* **Agentic Verification:** A dedicated "Auditor" agent verifies all AI-generated PRs against security benchmarks before deployment.
* **MCP Integration:** Uses the Model Context Protocol (MCP) to allow agents to securely interact with the local filesystem and database schemas.

## 3. The Tech Stack
* **Orchestration:** [LangGraph](https://www.langchain.com/langgraph) (Stateful Agent Workflows)
* **Models:** Claude 3.5 Sonnet (Fixing), o1-mini (Auditing), Llama 3.1 8B (Triage)
* **Database:** PostgreSQL with `pgvector` for SOP retrieval
* **Monitoring:** Prometheus & Grafana
* **Infrastructure:** Docker

---

## 4. System Architecture

### Phase 1: The Observability Loop (Sentry)
The Sentry agent monitors the live FastAPI application. When a 5xx error or a latency spike is detected, it captures the stack trace and environment state.

### Phase 2: Semantic Routing
The system passes the error signature through a **Cost Router**. 
* *Low Complexity:* (e.g., environmental config) -> Local Llama.
* *High Complexity:* (e.g., race conditions) -> Claude 3.5 Sonnet.

### Phase 3: The Repair & Audit Cycle
1.  **Mechanic Agent:** Writes the unit test that reproduces the failure, then writes the fix.
2.  **Auditor Agent:** Performs a "static analysis" of the fix to ensure no security regressions (e.g., OWASP Top 10) were introduced.

---

## 5. Cost-Resiliency Metrics
This project demonstrates "Green AI" principles by minimizing token spend:
| Task | Model Used | Estimated Cost |
| :--- | :--- | :--- |
| Monitoring | Local Llama 3.1 | $0.00 |
| Triage | Claude 3 Haiku | $0.0002 |
| Complex Fix | Claude 3.5 Sonnet | $0.04 |
| **Total per incident** | | **<$0.05** |

---

## 6. Getting Started
1.  **Clone the repo:** `git clone https://github.com/username/sentinel-v`
2.  **Configure Environment:** Create a `.env` file with your `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`.
3.  **Spin up the Infrastructure:** `docker-compose up -d`
4.  **Inject a Failure:** Run `python scripts/chaos_monkey.py` to break a specific API endpoint and watch the agents go to work.

---

## 7. Future-Proof Engineering Reflections
*Self-critique of the AI-human collaborative process:*
* *Why I chose Agentic loops over simple scripts.*
* *How I mitigated AI hallucinations through "human-in-the-loop" checkpoints.*
* *Analysis of the cost savings achieved via Semantic Routing.*