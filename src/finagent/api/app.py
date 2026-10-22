"""Versioned local API, with business logic delegated to Service."""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from finagent.api.schemas import (
    HistoryResponse,
    ProfileInput,
    RecommendationResponse,
    RuleResponse,
    TodayResponse,
)
from finagent.domain.models import UserProfile
from finagent.persistence.store import Store, get, history
from finagent.service import Service

load_dotenv()


class Payload(BaseModel):
    model_config = ConfigDict(extra="allow")


class Decision(BaseModel):
    amount: int | None = Field(default=None, strict=True, ge=0)
    schedule_day: int | None = Field(default=None, ge=1, le=28)
    reason: str = Field(default="", max_length=500)


class Message(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class Replay(BaseModel):
    days: int = Field(default=7, ge=1, le=31)


class Answer(BaseModel):
    answer: int = Field(ge=0)


def create_app(db_url: str | None = None) -> FastAPI:
    app = FastAPI(
        title="FinAgent",
        version="0.1.0",
        description="Local educational prototype. All actions are simulated.",
    )
    service = Service(Store(db_url or os.getenv("FINAGENT_DB", "sqlite:///finagent.db")))
    app.state.service = service

    @app.exception_handler(ValueError)
    async def invalid(request: Any, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=422, content={"error": {"code": "validation", "message": str(exc)}}
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Any, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation",
                    "message": "; ".join(e["msg"] for e in exc.errors()),
                }
            },
        )

    @app.get("/health", response_model=Payload)
    def health() -> Any:
        return {"status": "ok"}

    @app.post("/api/v1/demo/{key}", response_model=Payload)
    def demo(key: str) -> Any:
        return service.reset_persona(key)

    @app.get("/api/v1/profile", response_model=UserProfile)
    def profile() -> Any:
        with service.store.transaction() as s:
            return service.profile(s).to_dict()

    @app.put("/api/v1/profile", response_model=UserProfile)
    def update(body: ProfileInput) -> Any:
        return service.update_profile(body.root.to_dict())

    @app.post("/api/v1/assumptions/confirm", response_model=Payload)
    def confirm(body: Payload) -> Any:
        return service.confirm(body.model_dump().get("merchant", ""))

    @app.get("/api/v1/today", response_model=TodayResponse)
    def today() -> Any:
        return service.today()

    @app.post("/api/v1/recommendations/refresh", response_model=Payload)
    def refresh() -> Any:
        with service.store.transaction() as s:
            return {"recommendation": service.refresh(s)}

    @app.post("/api/v1/recommendations/{rec_id}/{action}", response_model=RecommendationResponse)
    def decision(rec_id: str, action: str, body: Decision) -> Any:
        return service.decide(rec_id, action, **body.model_dump())

    @app.get("/api/v1/rules", response_model=list[RuleResponse])
    def rules() -> Any:
        with service.store.transaction() as s:
            return get(s, "rules", [])

    @app.post("/api/v1/rules", response_model=Payload)
    def new_rule(body: Payload) -> Any:
        return service.save_rule(body.model_dump())

    @app.patch("/api/v1/rules/{rule_id}", response_model=Payload)
    def patch_rule(rule_id: str, body: Payload) -> Any:
        return service.save_rule(body.model_dump(), rule_id)

    @app.get("/api/v1/history", response_model=list[HistoryResponse])
    def events(type: str | None = None) -> Any:
        with service.store.transaction() as s:
            return history(s, type)

    @app.post("/api/v1/assistant/messages", response_model=Payload)
    def assistant(body: Message) -> Any:
        return service.chat(body.message)

    @app.get("/api/v1/lessons/today", response_model=Payload)
    def lesson() -> Any:
        return {"lesson": service.today()["lesson"]}

    @app.post("/api/v1/lessons/{lesson_id}/answer", response_model=Payload)
    def answer(lesson_id: str, body: Answer) -> Any:
        return service.answer_lesson(lesson_id, body.answer)

    @app.post("/api/v1/import/statement", response_model=Payload)
    async def import_statement(
        file: UploadFile = File(...), mapping: str = Form("{}"), keywords: str = Form("{}")
    ) -> Any:
        content = await file.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024:
            raise ValueError("Use a CSV smaller than 5 MB")
        return service.import_statement(content, json.loads(mapping), json.loads(keywords))

    @app.get("/api/v1/import/summary", response_model=Payload)
    def summary() -> Any:
        with service.store.transaction() as s:
            return get(s, "import_summary", {})

    @app.post("/api/v1/replay/advance", response_model=Payload)
    def replay(body: Replay) -> Any:
        return service.replay(body.days)

    @app.delete("/api/v1/data", response_model=Payload)
    def delete_data() -> Any:
        service.delete_data()
        return {"deleted": True}

    if Path("frontend/dist").exists():
        app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
    return app


app = create_app()
