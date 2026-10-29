import os
import secrets
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4
from urllib.parse import urlsplit
from fastapi import Body, Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import Field
from .domain import (Record, Snapshot, PositiveMoney, Money, Obligation, Debt, StateView, PreviewView, Transaction, MAX_TRANSACTIONS,
                     fixture, view as legacy_view, accept, complete, eligibility, merge_transactions)
from .debt import DebtSimulationView, compare_and_simulate
from .decision import DecisionEvaluationSnapshot, evaluate_decision
from .lessons import (LessonDetailView, LessonProgressCommand, LessonsListView,
                      get_lesson_detail, list_lessons, record_lesson_progress)
from .store import Store, Conflict
from .ai import Quotas, MODELS, ROUTES, enabled
from .imports import ImportPreview, ImportError_, build_preview, MAX_BYTES, keyword_category
from .chat import ChatRequest, ChatReply, chat
from .personal import install_personal
from .observations import ObservationsView, analyse
from .planning import install_planning
from .auth import SupabaseJWTConfig, SupabaseJWTVerifier, local_owner
from .frontend import install_frontend
from .fx_routes import install_fx
from .logging_setup import install_request_logging


class Command(Record):
    revision: int = Field(ge=0, strict=True)


class SnapshotCommand(Command):
    snapshot: Snapshot


class AmountCommand(Command):
    amount: PositiveMoney


class IncomeCommand(AmountCommand):
    event_id: str = Field(min_length=8, max_length=80)
    received_on: date
    already_in_balance: bool


class CostCommand(Command):
    obligation: Obligation


class BillDone(Command):
    paid: bool


class DebtCommand(Command):
    debt: Debt


class DebtSimulateRequest(Record):
    recurring_extra_cents: Money = 0
    one_off_extra_cents: Money = 0
    target_debt_id: str | None = Field(default=None, max_length=80)
    debts: list[Debt] | None = Field(default=None, max_length=50)


class DebtsView(Record):
    revision: int
    debts: list[Debt]
    comparison: DebtSimulationView


class DecisionEvaluateCommand(Command):
    policy: str = Field(default="fifth-of-available-v1", min_length=1, max_length=60)


class ConfirmCommand(Command):
    field: Literal["debt_known", "obligations_complete"]


class ApplyImport(Command):
    cash: Money | None = None
    obligation_ids: list[str] = Field(default_factory=list, max_length=20)


class UploadBase64(Record):
    filename: str = Field(min_length=1, max_length=180)
    content_type: str | None = None
    data_base64: str = Field(min_length=1, max_length=22_000_000)


class Preview(Record):
    amount: Money


class TransactionsView(Record):
    transactions: list[Transaction]
    total: int


class ModelUsage(Record):
    model: str
    requests_today: int
    daily_limit: int
    requests_last_minute: int
    tokens_last_minute: int
    cooling_down: bool


class AIStatus(Record):
    enabled: bool
    routes: dict[str, str]
    models: list[ModelUsage]


def create_app(database_url: str | None = None, demo_token: str | None = None, today=None, local_dir: Path | None = None,
               frontend_origins: list[str] | None = None, jwt_config: SupabaseJWTConfig | None = None,
               jwks_transport=None, auth_clock=None, fx_rates=None) -> FastAPI:
    mode = os.getenv('APP_MODE', 'demo')
    if mode not in ('demo', 'local', 'cloud'):
        raise RuntimeError('APP_MODE must be local or cloud (demo is a deprecated local alias).')
    verifier = None
    selected_database = database_url or os.getenv('DATABASE_URL')
    if mode == 'cloud':
        verifier = SupabaseJWTVerifier(jwt_config or SupabaseJWTConfig.from_env(), transport=jwks_transport, clock=auth_clock)
        if not selected_database:
            raise RuntimeError('Cloud mode requires an explicit database URL; local fallback is disabled.')
    origins = ["http://localhost:8081", "http://localhost:19006"] if frontend_origins is None else frontend_origins
    for origin in origins:
        parsed = urlsplit(origin)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or '*' in origin:
            raise ValueError('Frontend origins must be exact HTTP(S) origins, without paths or wildcards.')
        parsed.port  # Reject malformed port numbers before creating storage.
    local = local_dir or Path(__file__).resolve().parents[3] / ".local"
    local.mkdir(parents=True, exist_ok=True)
    token = demo_token or os.getenv("DEMO_API_TOKEN")
    if mode != 'cloud' and (not token or len(token) < 24):
        raise RuntimeError("Set DEMO_API_TOKEN to a random token of at least 24 characters. Use scripts/setup-local.py.")
    clock = today or date.today
    store = Store(selected_database or f"sqlite:///{local / 'demo.db'}")
    quotas = Quotas(local / "quota.db")
    app = FastAPI(title="Vela local API", version="0.2.0")
    app.state.store = store
    app.state.quotas = quotas
    app.add_middleware(CORSMiddleware, allow_origins=origins,
                       allow_methods=["GET", "POST", "PUT", "DELETE"],
                       allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Correlation-ID"],
                       expose_headers=["X-Correlation-ID"])
    install_request_logging(app, origins)

    def owner(authorization: Annotated[str | None, Header()] = None) -> str:
        return verifier.owner(authorization) if verifier is not None else local_owner(authorization, token)

    def idempotency(idempotency_key: Annotated[str, Header(min_length=8, max_length=100)]) -> str:
        return idempotency_key

    @app.exception_handler(Conflict)
    async def conflict_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def value_handler(request, exc):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    def require_legacy(s):
        if s.personal.planning.active:
            raise HTTPException(409, 'Use /v2/planning for your current shared account plan.')

    def view(s, today):
        if not s.personal.planning.active:
            return legacy_view(s, today)
        # The original snapshot remains in storage/export, never presented as current facts.
        data = legacy_view(s.model_copy(update={'snapshot': None, 'actions': []}), today)
        data['recommendation'] = {'kind': 'clarify', 'amount': 0, 'message': 'Open your shared account plan for current facts.'}
        return data

    def mutate_legacy(who, key, revision, command, apply, render):
        # Check the current mode before Store can return a pre-adoption receipt.
        # Hold the same reentrant lock through lookup/mutation/render so adoption
        # cannot race this check. Receipts and original history remain untouched.
        with store.lock:
            active = store.read(who).personal.planning.active
            if active:
                if command['kind'] == 'evaluate_decision':
                    require_legacy(store.read(who))
                if command['kind'] not in ('import_analytics', 'add_debt', 'delete_debt', 'lesson_progress'):
                    raise ValueError('Use your shared account plan. Legacy money changes are disabled after adoption.')
            result = store.mutate(who, key, revision, command, apply, render)
            # Still-allowed commands may also have old receipts containing legacy
            # StateView/lesson context. Keep one-time effects, show current facts.
            return render(store.read(who)) if active else result

    def change(who, key, body, kind, apply, extra=None):
        def checked(s):
            if s.personal.planning.active and kind not in ('import_analytics', 'add_debt', 'delete_debt'):
                raise ValueError('Use your shared account plan. Legacy money changes are disabled after adoption.')
            apply(s)
            if s.personal.planning.active and kind in ('add_debt', 'delete_debt'):
                s.personal.planning.debts_confirmed = False
        return mutate_legacy(who, key, body.revision, {"kind": kind, **body.model_dump(mode="json"), **(extra or {})},
                            checked, lambda state: view(state, clock()))

    def rebuild(s, **changes) -> Snapshot:
        return Snapshot.model_validate({**s.snapshot.model_dump(), **changes})

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "cloud" if mode == 'cloud' else 'local', "ai_enabled": enabled()}

    @app.get("/v1/state", response_model=StateView)
    def get_state(who=Depends(owner)):
        return view(store.read(who), clock())

    @app.post("/v1/demo", response_model=StateView)
    def load_demo(body: Command, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            if s.snapshot is not None:
                raise ValueError("You already have data. Delete it in Settings before loading the example.")
            s.snapshot = fixture(clock())
        return change(who, key, body, "load_demo", apply)

    @app.put("/v1/snapshot", response_model=StateView)
    def snapshot(body: SnapshotCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            if body.snapshot.as_of != clock():
                raise ValueError("Use today's balance.")
            # Saved allocation is authoritative once plans exist; prevent accidental double counting.
            if s.snapshot and any(a.status == "completed" for a in s.actions) and body.snapshot.saved != s.snapshot.saved:
                raise ValueError("Keep the amount already set aside unchanged; it's tracked by your completed steps.")
            s.snapshot = body.snapshot
            s.deferred = False
        return change(who, key, body, "snapshot", apply)

    @app.post("/v1/confirm", response_model=StateView)
    def confirm(body: ConfirmCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            if not s.snapshot:
                raise ValueError("Add your balance first.")
            setattr(s.snapshot, body.field, True)
        return change(who, key, body, "confirm", apply)

    @app.post("/v1/actions", response_model=StateView)
    def accept_action(body: AmountCommand, who=Depends(owner), key=Depends(idempotency)):
        return change(who, key, body, "accept", lambda s: accept(s, body.amount, str(uuid4()), clock()))

    @app.post("/v1/actions/{action_id}/complete", response_model=StateView)
    def complete_action(action_id: str, body: Command, who=Depends(owner), key=Depends(idempotency)):
        return change(who, key, body, "complete", lambda s: complete(s, action_id, clock()), {"action_id": action_id})

    @app.post("/v1/actions/{action_id}/cancel", response_model=StateView)
    def cancel_action(action_id: str, body: Command, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            action = next((a for a in s.actions if a.id == action_id), None)
            if not action or action.status != "planned":
                raise ValueError("Only a planned step can be cancelled.")
            action.status = "cancelled"
        return change(who, key, body, "cancel", apply, {"action_id": action_id})

    @app.post("/v1/defer", response_model=StateView)
    def defer(body: Command, who=Depends(owner), key=Depends(idempotency)):
        return change(who, key, body, "defer", lambda s: setattr(s, "deferred", True))

    @app.post("/v1/income", response_model=StateView)
    def income(body: IncomeCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            if not s.snapshot:
                raise ValueError("Add your balance first.")
            if body.received_on > clock():
                raise ValueError("Expected income cannot increase today's balance.")
            if body.event_id in s.income_ids:
                raise ValueError("This income is already recorded.")
            if not body.already_in_balance:
                if body.received_on <= s.snapshot.as_of:
                    raise ValueError("Income on or before the balance date needs a refreshed balance, not an addition.")
                s.snapshot.cash += body.amount
            s.income_ids.append(body.event_id)
            s.deferred = False
        return change(who, key, body, "income", apply)

    @app.post("/v1/obligations", response_model=StateView)
    def obligation(body: CostCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            if not s.snapshot:
                raise ValueError("Add your balance first.")
            s.snapshot = rebuild(s, obligations=[*s.snapshot.model_dump()["obligations"], body.obligation.model_dump()])
            s.deferred = False
        return change(who, key, body, "obligation", apply)

    @app.post("/v1/obligations/{obligation_id}/done", response_model=StateView)
    def obligation_done(obligation_id: str, body: BillDone, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            if not s.snapshot:
                raise ValueError("Add your balance first.")
            bill = next((o for o in s.snapshot.obligations if o.id == obligation_id), None)
            if not bill:
                raise ValueError("Bill not found.")
            rest = [o.model_dump() for o in s.snapshot.obligations if o.id != obligation_id]
            # Paying a bill lowers cash by the same amount; removing a mistaken bill does not.
            cash = s.snapshot.cash - bill.amount if body.paid else s.snapshot.cash
            if cash < 0:
                raise ValueError("Your cash is lower than this bill. Update your balance instead.")
            s.snapshot = rebuild(s, obligations=rest, cash=cash)
        return change(who, key, body, "bill_paid" if body.paid else "bill_removed", apply, {"obligation_id": obligation_id})

    @app.post("/v1/preview", response_model=PreviewView)
    def preview(body: Preview, who=Depends(owner)):
        s = store.read(who)
        require_legacy(s)
        data = view(s, clock())
        allowed = (s.snapshot is not None and eligibility(s, clock()) is None and 0 < body.amount <= data["available"]
                   and body.amount <= max(0, s.snapshot.goal_target-s.snapshot.saved))
        return {"revision": s.revision, "amount": body.amount, "eligible": allowed,
                "remaining": data["available"]-body.amount, "goal_after": (s.snapshot.saved if s.snapshot else 0)+body.amount}

    # ---------- debts ----------

    @app.get("/v1/debts", response_model=DebtsView)
    def get_debts(who=Depends(owner)):
        s = store.read(who)
        return {
            "revision": s.revision,
            "debts": s.debts,
            "comparison": compare_and_simulate(s.debts, revision=s.revision),
        }

    @app.post("/v1/debts", response_model=StateView)
    def add_debt(body: DebtCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            if any(d.id == body.debt.id for d in s.debts):
                raise ValueError("Debt ID must be unique.")
            s.debts.append(body.debt)
            s.deferred = False
        return change(who, key, body, "add_debt", apply)

    @app.delete("/v1/debts/{debt_id}", response_model=StateView)
    def delete_debt(
        debt_id: str,
        body: Annotated[Command | None, Body()] = None,
        revision: Annotated[int | None, Query(ge=0, strict=True)] = None,
        who=Depends(owner),
        key=Depends(idempotency),
    ):
        rev = body.revision if body is not None else revision
        if rev is None:
            raise ValueError("Provide expected revision in request body or query parameter.")
        cmd = Command(revision=rev)

        def apply(s):
            if not any(d.id == debt_id for d in s.debts):
                raise ValueError("Debt not found.")
            s.debts = [d for d in s.debts if d.id != debt_id]
            s.deferred = False

        return change(who, key, cmd, "delete_debt", apply, {"debt_id": debt_id})

    @app.post("/v1/debts/simulate", response_model=DebtSimulationView)
    def simulate_debts(body: DebtSimulateRequest, who=Depends(owner)):
        s = store.read(who)
        debts = body.debts if body.debts is not None else s.debts
        return compare_and_simulate(
            debts=debts,
            revision=s.revision,
            recurring_extra_cents=body.recurring_extra_cents,
            one_off_extra_cents=body.one_off_extra_cents,
            target_debt_id=body.target_debt_id,
        )

    # ---------- decision engine ----------

    @app.get("/v1/decision", response_model=DecisionEvaluationSnapshot)
    def get_decision(
        policy: Annotated[str, Query(min_length=1, max_length=60)] = "fifth-of-available-v1",
        who=Depends(owner),
    ):
        s = store.read(who)
        require_legacy(s)
        return evaluate_decision(s, clock(), policy=policy)

    @app.post("/v1/decision/evaluate", response_model=DecisionEvaluationSnapshot)
    def record_decision_evaluation(
        body: DecisionEvaluateCommand,
        who=Depends(owner),
        key=Depends(idempotency),
    ):
        snap_holder: dict[str, DecisionEvaluationSnapshot] = {}

        def apply(s):
            require_legacy(s)
            snap = evaluate_decision(s, clock(), policy=body.policy)
            snap_holder["snapshot"] = snap
            s.history.append({"event": "decision_snapshot", "revision": s.revision + 1, "snapshot": snap.model_dump(mode="json")})

        def render(s):
            return snap_holder["snapshot"].model_dump(mode="json")

        return mutate_legacy(
            who,
            key,
            body.revision,
            {"kind": "evaluate_decision", **body.model_dump(mode="json")},
            apply,
            render,
        )

    # ---------- lessons (Journey E) ----------

    @app.get("/v1/lessons", response_model=LessonsListView)
    def get_lessons(
        action_id: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
        who=Depends(owner),
    ):
        s = store.read(who)
        return list_lessons(s, clock(), action_id=action_id)

    @app.get("/v1/lessons/{lesson_id}", response_model=LessonDetailView)
    def get_lesson(lesson_id: str, who=Depends(owner)):
        s = store.read(who)
        try:
            return get_lesson_detail(lesson_id, s, clock())
        except KeyError as exc:
            raise HTTPException(404, "Lesson not found.") from exc

    @app.post("/v1/lessons/{lesson_id}/progress", response_model=LessonDetailView)
    def save_lesson_progress(
        lesson_id: str,
        body: LessonProgressCommand,
        idempotency_key: Annotated[str | None, Header(min_length=8, max_length=100)] = None,
        who=Depends(owner),
    ):
        current_state = store.read(who)
        try:
            get_lesson_detail(lesson_id, current_state, clock())
        except KeyError as exc:
            raise HTTPException(404, "Lesson not found.") from exc

        expected_rev = body.revision if body.revision is not None else current_state.revision
        eff_key = idempotency_key or f"lesson-prog-{lesson_id}-{body.selected_index}-{body.completed}-{expected_rev}"

        def apply(s):
            record_lesson_progress(
                s,
                lesson_id=lesson_id,
                today=clock(),
                selected_index=body.selected_index,
                completed=body.completed,
            )

        def render(s):
            return get_lesson_detail(lesson_id, s, clock()).model_dump(mode="json")

        return mutate_legacy(
            who,
            eff_key,
            expected_rev,
            {"kind": "lesson_progress", "lesson_id": lesson_id, **body.model_dump(mode="json")},
            apply,
            render,
        )

    # ---------- statements ----------

    @app.post("/v1/imports", response_model=ImportPreview)
    async def upload(file: Annotated[UploadFile, File()], who=Depends(owner)):
        data = await file.read(MAX_BYTES + 1)
        preview_id = f"imp-{int(time.time()*1000):014d}-{uuid4().hex[:6]}"
        try:
            result = await build_preview(data, file.filename or "statement", file.content_type, quotas, clock(), preview_id)
        except ImportError_ as exc:
            raise HTTPException(422, str(exc)) from exc
        store.save_preview(who, preview_id, result.model_dump_json())
        return result

    @app.post("/v1/imports/base64", response_model=ImportPreview)
    async def upload_base64(body: UploadBase64, who=Depends(owner)):
        import base64
        raw = body.data_base64.split(",", 1)[-1]
        try:
            data = base64.b64decode(raw, validate=False)
        except Exception as exc:
            raise HTTPException(422, "Could not decode uploaded file.") from exc
        preview_id = f"imp-{int(time.time()*1000):014d}-{uuid4().hex[:6]}"
        try:
            result = await build_preview(data, body.filename, body.content_type, quotas, clock(), preview_id)
        except ImportError_ as exc:
            raise HTTPException(422, str(exc)) from exc
        store.save_preview(who, preview_id, result.model_dump_json())
        return result

    @app.get("/v1/imports/{preview_id}", response_model=ImportPreview)
    def get_import(preview_id: str, who=Depends(owner)):
        payload = store.get_preview(who, preview_id)
        if not payload:
            raise HTTPException(404, "This upload has expired. Upload the file again.")
        return ImportPreview.model_validate_json(payload)

    @app.post("/v1/imports/{preview_id}/apply", response_model=StateView)
    def apply_import(preview_id: str, body: ApplyImport, who=Depends(owner), key=Depends(idempotency)):
        payload = store.get_preview(who, preview_id)
        if not payload:
            raise HTTPException(404, "This upload has expired. Upload the file again.")
        imported = ImportPreview.model_validate_json(payload)

        def apply(s):
            today = clock()
            merge_transactions(s, imported.transactions)
            chosen = [r for r in imported.recurring if r.id in body.obligation_ids]
            if s.snapshot is None:
                if body.cash is None:
                    raise ValueError("Enter your current balance to finish setting up.")
                s.snapshot = Snapshot(as_of=today, horizon=today+timedelta(days=30), cash=body.cash,
                                      protected=min(10000, body.cash), goal_target=100000, provenance="import")
            elif body.cash is not None:
                kept = [o.model_dump() for o in s.snapshot.obligations if o.due >= today]
                s.snapshot = rebuild(s, cash=body.cash, as_of=today, obligations=kept,
                                     horizon=max(s.snapshot.horizon, today), provenance="import")
            existing = {o.id for o in s.snapshot.obligations}
            chosen = [r for r in chosen if r.id not in existing]
            if chosen:
                # Stretch the plan-through date to cover the selected bills (max 93 days).
                limit = s.snapshot.as_of + timedelta(days=93)
                horizon = min(limit, max(s.snapshot.horizon, *(r.next_due for r in chosen)))
                new = [Obligation(id=r.id, label=r.label, amount=r.amount, due=r.next_due, kind=r.kind).model_dump()
                       for r in chosen if s.snapshot.as_of <= r.next_due <= horizon]
                s.snapshot = rebuild(s, horizon=horizon, obligations=[*s.snapshot.model_dump()["obligations"], *new])
            s.deferred = False
        return change(who, key, body, "import", apply, {"preview_id": preview_id})

    @app.get("/v1/transactions", response_model=TransactionsView)
    def transactions(limit: int = 300, offset: Annotated[int, Query(ge=0)] = 0, who=Depends(owner)):
        txns = store.read(who).transactions
        return {"transactions": txns[offset:offset+max(1, min(limit, 3000))], "total": len(txns)}

    @app.post('/v2/imports/{preview_id}/apply', response_model=StateView)
    def apply_analytics(preview_id: str, body: Command, who=Depends(owner), key=Depends(idempotency)):
        payload = store.get_preview(who, preview_id)
        if not payload:
            raise HTTPException(404, 'This upload has expired. Upload the file again.')
        imported = ImportPreview.model_validate_json(payload)
        if imported.currency != 'EUR':
            raise ValueError('Only EUR statement analytics is supported here. No conversion was applied.')
        def apply(s):
            keys = {(t.date, t.amount, t.description.lower()) for t in [*s.transactions, *imported.transactions]}
            if len(keys) > MAX_TRANSACTIONS:
                raise ValueError('The local analytical history limit was reached. No existing entries were removed.')
            merge_transactions(s, imported.transactions)
            # Upgrade previously imported, explicitly labelled refunds without changing
            # their original description, date, amount or any confirmed finances.
            for row in s.transactions:
                if row.source.startswith('import:') and row.category in ('income', 'other') and keyword_category(row.description, row.amount) == 'refunds':
                    row.category = 'refunds'
        return change(who, key, body, 'import_analytics', apply, {'preview_id': preview_id})

    @app.get('/v2/observations', response_model=ObservationsView)
    def observations(who=Depends(owner)):
        return analyse(store.read(who))

    # ---------- AI ----------

    @app.post("/v1/chat", response_model=ChatReply)
    async def assistant_chat(body: ChatRequest, who=Depends(owner)):
        s = store.read(who)
        require_legacy(s)
        return await chat(body, s, clock(), quotas)

    @app.get("/v1/ai/status", response_model=AIStatus)
    def ai_status(who=Depends(owner)):
        return {"enabled": enabled(), "routes": ROUTES, "models": quotas.usage()}

    # ---------- data rights ----------

    @app.get("/v1/export")
    def export(who=Depends(owner)):
        return JSONResponse(store.read(who).model_dump(mode="json"), headers={"Content-Disposition": "attachment; filename=vela-export.json"})

    @app.delete("/v1/data")
    def erase(who=Depends(owner)):
        store.erase(who)
        return {"status": "deleted", "scope": "Balance, bills, plans, transactions and pending uploads. Anonymous AI usage counters are kept."}

    install_personal(app, store, owner, idempotency, clock)
    install_planning(app, store, owner, idempotency, clock)
    install_frontend(app, store, owner, clock)
    install_fx(app, store, owner, clock, rates=fx_rates)
    return app
