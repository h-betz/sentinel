from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from toy_app.app.api.router import api_router

app = FastAPI(
    title="Sentinel E-Commerce API",
    description="E-Commerce API with intentional bugs for debugging practice",
    version="1.0.0",
)

# Initialize Prometheus instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)

# Instrument the app and expose /metrics endpoint
instrumentator.instrument(app).expose(app, include_in_schema=False)

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
