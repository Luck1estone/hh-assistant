from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from backend.app.api.resumes import (
    router as resumes_router,
)

from backend.app.api.vacancies import (
    router as vacancies_router,
)

from backend.app.storage.db import (
    init_db,
)


app = FastAPI(
    title="HH Job Assistant API",
    version="0.3.0",
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


init_db()


app.include_router(
    resumes_router
)

app.include_router(
    vacancies_router
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "HH Job Assistant",
        "version": "0.3.0",
    }