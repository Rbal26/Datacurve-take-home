from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="PR Telemetry Trace API",
    version="1.0.0",
    description="Backend for collecting and validating developer debugging traces",
    max_body_size=10_000_000
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "PR Telemetry Trace API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}