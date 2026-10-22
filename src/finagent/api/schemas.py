"""OpenAPI response contracts; domain dataclasses remain framework independent."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, RootModel

from finagent.domain.models import Candidate, UserProfile


class ProfileInput(RootModel[UserProfile]):
    pass


class Overview(BaseModel):
    safe_to_spend: int
    reserved: int
    buffer_after: int
    days_to_income: int
    emergency_saved: int
    emergency_target: int
    cushion_months: str


class Considered(BaseModel):
    candidate: Candidate
    score: str


class RecommendationResponse(BaseModel):
    id: str
    user_id: str
    created_at: str
    status: Literal["pending", "accepted", "adjusted", "declined", "superseded"]
    decision_at: str | None
    adjustment_params: dict[str, Any] | None
    chosen_candidate_id: str
    chosen: Candidate
    considered: list[Considered]
    reason_facts: dict[str, int]
    explanation_text: str
    alternative: str
    alternative_reason: str
    do_nothing: str
    mode: str


class RuleResponse(BaseModel):
    id: str
    user_id: str
    name: str
    trigger: dict[str, str]
    amount: int
    account: str
    status: Literal["active", "paused"]
    affordability_floor: int
    created_from_recommendation: str | None


class HistoryResponse(BaseModel):
    id: int
    timestamp: str
    type: str
    payload: dict[str, Any]


class TodayResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    profile: UserProfile
    date: str
    demo: bool
    provider: str
    overview: Overview
    recommendation: RecommendationResponse | None
    guard: dict[str, str] | None
    lesson: dict[str, Any] | None
    rules: list[RuleResponse]
    history: list[HistoryResponse]
    analysis: dict[str, Any]
    disclaimer: str
