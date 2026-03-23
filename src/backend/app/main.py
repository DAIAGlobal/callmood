from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .api.routes import auth, calls, metrics, analysisv2
from .db import Base, engine

settings = get_settings()

app = FastAPI(title=settings.app_name)
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(calls.router, prefix=settings.api_v1_prefix)
app.include_router(metrics.router, prefix=settings.api_v1_prefix)
app.include_router(analysisv2.router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
