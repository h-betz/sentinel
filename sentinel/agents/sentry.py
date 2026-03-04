import httpx
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from typing import Dict

"""
Monitors application logs and metrics, raises the alarm when an anomaly is detected
Should use a lighter-weight model that is faster
"""


@dataclass
class SentryDeps:
    app_url: str
    prometheus_url: str


class Sentry:

    def __init__(self):
        self.agent = Agent(
            "anthropic:claude-3-5-sonnet",
            system_prompt="You are a Sentry. Your job is to check if the App is healthy.",
            output_type=Dict,
        )
        self._register_tools()

    def _register_tools(self):
        """Hidden method to attach tools to the internal agent."""

        @self.agent.tool
        async def check_latency(ctx: RunContext[SentryDeps]) -> Dict:
            """
            Checks App response time

            """
            query = "histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))"
            url = f"{ctx.deps.prometheus_url}/api/v1/query"

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(url, params={"query": query})
                    response.raise_for_status()
                    data = response.json()

                    results = data.get("data", {}).get("result", [])
                    if not results:
                        return {}

                    # Prometheus returns values as [timestamp, "value_string"]
                    # We convert the second element to a float (seconds -> milliseconds)
                    value_sec = float(results[0].get("value", {})[1])
                    value_ms = round(value_sec / 1000, 2)
                    if value_ms >= 500:
                        return {
                            "escalation": "ESCALATE",
                            "error_type": "LATENCY_SPIKE",
                            "raw_data": data,
                        }
                    return {}
                except Exception as e:
                    return {"error": "Unhandled Exception", "context": str(e)}

        @self.agent.tool
        async def check_server_errors(ctx: RunContext[SentryDeps]) -> Dict:
            """
            Checks for unhandled server errors (5xx) in the past 5 minutes
            If ANY errors have been found, we need to return the following data:
            {
                "escalation": "ESCALATE",
                "error_type": "5xx_SPIKE",
                "raw_data": data
            }
            """
            query = 'sum(increase(http_requests_total{status=~"5.."}[5m]))'
            url = f"{ctx.deps.prometheus_url}/api/v1/query"

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(url, params={"query": query})
                    response.raise_for_status()
                    data = response.json()

                    results = data.get("data", {}).get("result", [])
                    if not results:
                        return {}

                    error_count = float(results[0].get("value", {})[1])
                    if error_count >= 0:
                        return {
                            "escalation": "ESCALATE",
                            "error_type": "5xx_SPIKE",
                            "raw_data": data,
                        }
                    return {}
                except Exception as e:
                    return {"error": "Unhandled Exception", "context": str(e)}

    async def run_audit(self, app_url) -> Dict:
        """Public method to start an observation task"""
        deps = SentryDeps(app_url=app_url, prometheus_url="http://localhost:9090")

        # Start the monitoring run
        # The agent will call all of its @self.agent.tool functions here
        result = await self.agent.run("Perform a health check.", deps=deps)
        if result.output.get("escalation") == "ESCALATE":
            return result.output
        return {"status": "OK"}
