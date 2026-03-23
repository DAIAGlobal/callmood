"""
Placeholder FastAPI wiring.

Goal: expose DAIA use-cases (Audit, BatchAudit) via HTTP without
introducing framework dependencies into the domain or application layers.
"""

from fastapi import FastAPI

app = FastAPI(title="DAIA API (placeholder)", version="0.0.1")


@app.get("/health")
def health():
    return {"status": "ok"}


# TODO: Wire BatchAuditService via adapters/DTOs when API is prioritized.
