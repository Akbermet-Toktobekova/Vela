"""Frontend projections over one stored revision; no second financial state."""
from datetime import date
from typing import Literal
from fastapi import Depends
from pydantic import Field
from .domain import Record, Summary, summary
from .personal import PersonalView
from .planning import PlanningView, planning_view
from .observations import ObservationsView, analyse
from .lessons import LessonsListView, list_lessons


class FrontendCapabilities(Record):
    mode: Literal['local_single_user'] = 'local_single_user'
    planning_currency: Literal['EUR'] = 'EUR'
    account_currencies: list[Literal['EUR', 'HUF']] = Field(default_factory=lambda: ['EUR', 'HUF'])
    assistant: Literal['deterministic_read_only'] = 'deterministic_read_only'
    import_effect: Literal['analytics_only'] = 'analytics_only'
    cloud_otp: bool = False
    multi_user: bool = False
    persistent_chat: bool = False
    bank_connections: bool = False
    money_transfers: bool = False
    server_reminders: bool = False
    multi_goal: bool = False
    fx_in_plan: bool = False


class AssistantContext(Record):
    revision: int
    as_of: date
    source: Literal['local_verified_facts'] = 'local_verified_facts'
    plan: PlanningView
    recorded_activity: Summary
    observations: ObservationsView
    lessons: LessonsListView
    note: str = ('Recorded activity totals cover the 30 days ending on the latest recorded transaction date; '
                 'transaction_count counts all stored rows. With no rows, zero totals do not establish zero spending. '
                 'Statements never change account balances or confirm future income. Observations may cover a longer recorded period.')


class FrontendView(Record):
    contract_version: Literal['local-frontend-v1'] = 'local-frontend-v1'
    revision: int
    as_of: date
    capabilities: FrontendCapabilities = Field(default_factory=FrontendCapabilities)
    personal: PersonalView
    assistant: AssistantContext


def assistant_context(state, today):
    return AssistantContext(revision=state.revision, as_of=today,
                            plan=planning_view(state, today), recorded_activity=summary(state),
                            observations=analyse(state), lessons=list_lessons(state, today))


def install_frontend(app, store, owner, clock):
    @app.get('/v2/frontend', response_model=FrontendView)
    def bootstrap(who=Depends(owner)):
        # Read once: all tabs use the same revision even if a write follows.
        state, today = store.read(who), clock()
        return FrontendView(revision=state.revision, as_of=today,
                            personal=PersonalView(revision=state.revision, data=state.personal),
                            assistant=assistant_context(state, today))

    @app.get('/v2/assistant/context', response_model=AssistantContext)
    def context(who=Depends(owner)):
        return assistant_context(store.read(who), clock())
