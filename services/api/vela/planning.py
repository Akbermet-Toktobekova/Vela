"""Local account-backed plan. Confirmed cash lives only in PersonalState.accounts."""
from datetime import date, timedelta
from typing import Annotated, Literal
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field

Money = Annotated[int, Field(strict=True, ge=0, le=1_000_000_000)]
Positive = Annotated[int, Field(strict=True, gt=0, le=1_000_000_000)]


class PlanningRecord(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)


class GoalInput(PlanningRecord):
    name: str = Field(min_length=1, max_length=60)
    target: Positive


class Goal(GoalInput):
    saved: Money = 0


class Bill(PlanningRecord):
    id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=100)
    amount: Positive
    currency: Literal['EUR'] = 'EUR'
    due: date
    status: Literal['unpaid', 'paid', 'cancelled'] = 'unpaid'
    source: Literal['manual', 'legacy'] = 'manual'


class Step(PlanningRecord):
    id: str = Field(min_length=1, max_length=80)
    account_id: str
    currency: Literal['EUR'] = 'EUR'
    amount: Positive
    status: Literal['planned', 'completed', 'cancelled'] = 'planned'
    created_on: date
    completed_on: date | None = None


class PlanningState(PlanningRecord):
    active: bool = False
    account_id: str | None = None
    horizon: date | None = None
    protected: Money | None = None
    bills_confirmed: bool = False
    debts_confirmed: bool = False
    goal: Goal | None = None
    bills: list[Bill] = Field(default_factory=list, max_length=100)
    steps: list[Step] = Field(default_factory=list, max_length=1000)
    deferred: bool = False


class PlanningCommand(PlanningRecord):
    revision: Annotated[int, Field(strict=True, ge=0)]


class ConfigurePlan(PlanningCommand):
    account_id: str
    horizon: date
    protected: Money | None
    bills_confirmed: bool
    debts_confirmed: bool
    goal: GoalInput | None = None


class AdoptLegacy(PlanningCommand):
    account_id: str
    confirm_finances: bool


class AddBill(PlanningCommand):
    id: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=100)
    amount: Positive
    currency: Literal['EUR']
    due: date


class PayBill(PlanningCommand):
    effect: Literal['subtract', 'already_in_balance']


class AddStep(PlanningCommand):
    id: str = Field(min_length=1, max_length=80)
    amount: Positive


class PreviewStep(PlanningRecord):
    amount: Positive


class PreviewStepView(PlanningRecord):
    revision: int
    amount: int
    eligible: bool
    remaining: int | None
    goal_after: int | None
    message: str


class AccountFacts(PlanningRecord):
    id: str
    name: str
    currency: Literal['EUR', 'HUF']
    balance: int | None
    confirmed_on: date | None


class LegacyFacts(PlanningRecord):
    cash: int
    saved: int
    goal_name: str
    goal_target: int
    bill_count: int
    planned_count: int


class PlanningView(PlanningRecord):
    revision: int
    planning: PlanningState
    account: AccountFacts | None
    currency: Literal['EUR'] = 'EUR'
    cash: int | None
    known_bills: int
    reserved: int
    goal_saved: int
    available: int | None
    needs_input: str | None
    recommendation_kind: Literal['clarify', 'save', 'maintain', 'shortfall', 'planned', 'goal_reached']
    recommendation_amount: int | None
    message: str
    can_complete: bool
    legacy: LegacyFacts | None
    policy: str = 'fifth-of-available-v1-provisional'


def chosen_account(state):
    return next((a for a in state.personal.accounts if a.id == state.personal.planning.account_id), None)


def missing_input(state, today):
    p, a = state.personal.planning, chosen_account(state)
    if not p.active:
        return 'Choose an EUR account and review your planning inputs.'
    if a is None or a.currency != 'EUR' or a.balance is None:
        return 'Confirm a known EUR account balance before a money step.'
    if a.confirmed_on != today:
        return 'Confirm or update this account balance for today before a money step.'
    if p.horizon is None or p.horizon < today:
        return 'Update your plan-through date.'
    if p.protected is None:
        return 'Choose the amount you want to keep protected; unknown is not zero.'
    if not p.debts_confirmed:
        return 'Check that required debt payments are included in your bills.'
    if not p.bills_confirmed:
        return 'Check that necessary bills through your plan date are included.'
    return None


def planning_view(state, today):
    from .domain import suggested_amount
    p, a = state.personal.planning, chosen_account(state)
    reserved = sum(s.amount for s in p.steps if s.status == 'planned')
    saved = p.goal.saved if p.goal else 0
    bills = sum(b.amount for b in p.bills if b.status == 'unpaid' and (p.horizon is None or b.due <= p.horizon))
    reason = missing_input(state, today)
    known = a is not None and a.currency == 'EUR' and a.balance is not None and p.protected is not None and p.bills_confirmed and p.debts_confirmed and p.horizon is not None
    available = a.balance - saved - p.protected - bills - reserved if known else None
    kind, amount, message = 'clarify', None, reason
    if not reason:
        if available < 0:
            kind, message = 'shortfall', 'Your confirmed commitments and allocations exceed this account balance. Review them before a new step.'
        elif any(s.status == 'planned' for s in p.steps):
            kind, message = 'planned', 'Keep your accepted step. Complete it only after you have earmarked the money yourself.'
        elif p.deferred:
            kind, message = 'maintain', 'No new step for now. Your money remains available.'
        elif p.goal is None:
            kind, message = 'maintain', 'No goal is required. Keep your money available, or add a goal when you want one.'
        elif p.goal.saved >= p.goal.target:
            kind, message = 'goal_reached', 'Your recorded goal allocation has reached its target.'
        else:
            amount = suggested_amount(available, p.goal.target-p.goal.saved)
            kind = 'save' if amount else 'maintain'
            message = 'A provisional local suggestion based on this account, protected money and confirmed bills.' if amount else 'Keep your money available; no new savings step fits right now.'
    legacy = None
    if not p.active and state.snapshot:
        s = state.snapshot
        legacy = LegacyFacts(cash=s.cash, saved=s.saved, goal_name=s.goal_name, goal_target=s.goal_target,
                             bill_count=len(s.obligations), planned_count=sum(a.status == 'planned' for a in state.actions))
    active = next((s for s in p.steps if s.status == 'planned'), None)
    return PlanningView(revision=state.revision, planning=p, account=AccountFacts(**a.model_dump()) if a else None,
                        cash=a.balance if a else None, known_bills=bills, reserved=reserved, goal_saved=saved,
                        available=available, needs_input=reason, recommendation_kind=kind,
                        recommendation_amount=amount, message=message or '',
                        can_complete=bool(active and p.goal and active.account_id == p.account_id and reason is None and available is not None
                                          and available >= 0 and active.amount <= p.goal.target-p.goal.saved), legacy=legacy)


def install_planning(app, store, owner, idempotency, clock):
    def change(who, key, body, kind, apply, **extra):
        return store.mutate(who, key, body.revision, {'kind': kind, **body.model_dump(mode='json'), **extra},
                            apply, lambda s: planning_view(s, clock()).model_dump(mode='json'))

    def require_plan(s):
        if not s.personal.planning.active:
            raise ValueError('Set up your shared account plan first.')
        return s.personal.planning

    @app.get('/v2/planning', response_model=PlanningView)
    def read(who=Depends(owner)):
        return planning_view(store.read(who), clock())

    @app.put('/v2/planning', response_model=PlanningView)
    def configure(body: ConfigurePlan, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            p = s.personal.planning
            if s.snapshot is not None and not p.active:
                raise ValueError('Review and adopt your existing legacy plan first; no history was replaced.')
            a = next((a for a in s.personal.accounts if a.id == body.account_id), None)
            if a is None or a.currency != 'EUR':
                raise ValueError('Choose an EUR account. HUF is shown separately without conversion.')
            if p.active and p.account_id != a.id:
                raise ValueError('This plan is linked to another account. Account reassignment needs a separate reconciliation.')
            if not clock() <= body.horizon <= clock()+timedelta(days=93):
                raise ValueError('Choose a plan date within the next93 days.')
            if any(b.status == 'unpaid' and b.due > body.horizon for b in p.bills):
                raise ValueError('The plan date must include your recorded unpaid bills.')
            saved = p.goal.saved if p.goal else 0
            if (saved or any(step.status == 'planned' for step in p.steps)) and (body.goal is None or body.goal.target < saved):
                raise ValueError('Keep your allocated goal and active step until they are separately reconciled.')
            p.account_id, p.horizon, p.protected = a.id, body.horizon, body.protected
            p.bills_confirmed, p.debts_confirmed = body.bills_confirmed, body.debts_confirmed
            p.goal = Goal(**body.goal.model_dump(), saved=saved) if body.goal else None
            p.active, p.deferred = True, False
        return change(who, key, body, 'shared_plan_configure', apply)

    @app.post('/v2/planning/adopt-legacy', response_model=PlanningView)
    def adopt(body: AdoptLegacy, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            if s.personal.planning.active:
                raise ValueError('Your shared plan is already set up.')
            if not body.confirm_finances or s.snapshot is None:
                raise ValueError('Review and explicitly confirm the legacy goal, allocations and bills first.')
            a = next((a for a in s.personal.accounts if a.id == body.account_id), None)
            old = s.snapshot
            if a is None or a.currency != 'EUR' or a.balance != old.cash or a.confirmed_on != clock():
                raise ValueError('Use a freshly confirmed EUR account with the same balance as the reviewed legacy plan. Reconcile differences first.')
            if old.horizon < clock():
                raise ValueError('Review and update the legacy plan-through date first.')
            s.personal.planning = PlanningState(active=True, account_id=a.id, horizon=old.horizon, protected=old.protected,
                bills_confirmed=old.obligations_complete, debts_confirmed=old.debt_known,
                goal=Goal(name=old.goal_name, target=old.goal_target, saved=old.saved), deferred=s.deferred,
                bills=[Bill(id=b.id, label=b.label, amount=b.amount, due=b.due, source='legacy') for b in old.obligations],
                steps=[Step(id=step.id, account_id=a.id, amount=step.amount, status=step.status,
                            created_on=step.created_on, completed_on=step.completed_on) for step in s.actions])
        return change(who, key, body, 'shared_plan_adopt_legacy', apply)

    @app.post('/v2/planning/bills', response_model=PlanningView)
    def add_bill(body: AddBill, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            p = require_plan(s)
            candidate = Bill(id=body.id, label=body.label.strip(), amount=body.amount, due=body.due)
            old = next((b for b in p.bills if b.id == body.id), None)
            if old:
                if (old.label, old.amount, old.due) != (candidate.label, candidate.amount, candidate.due):
                    raise ValueError('This bill identity was already used with different details.')
                return
            if p.horizon is None or body.due > p.horizon:
                raise ValueError('Choose a bill date within the plan-through date.')
            if len(p.bills) >= 100:
                raise ValueError('The local bill-history limit was reached; existing records were preserved.')
            p.bills.append(candidate)
            p.deferred = False
        return change(who, key, body, 'shared_plan_bill', apply)

    @app.post('/v2/planning/bills/{bill_id}/cancel', response_model=PlanningView)
    def cancel_bill(bill_id: str, body: PlanningCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            p = require_plan(s)
            b = next((b for b in p.bills if b.id == bill_id), None)
            if not b or b.status == 'paid':
                raise ValueError('Only an unpaid bill can be cancelled.')
            b.status = 'cancelled'
        return change(who, key, body, 'shared_plan_cancel_bill', apply, bill_id=bill_id)

    @app.post('/v2/planning/bills/{bill_id}/pay', response_model=PlanningView)
    def pay_bill(bill_id: str, body: PayBill, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            p = require_plan(s)
            b = next((b for b in p.bills if b.id == bill_id), None)
            if not b or b.status == 'cancelled':
                raise ValueError('Only an unpaid bill can be recorded as paid.')
            if b.status == 'paid':
                return
            if body.effect == 'subtract':
                a = chosen_account(s)
                if a is None or a.balance is None or a.confirmed_on != clock():
                    raise ValueError('Update this account balance for today first.')
                if a.balance < b.amount:
                    raise ValueError('This payment exceeds your confirmed balance. Reconcile the balance first.')
                a.balance -= b.amount
                a.confirmed_on = clock()
            b.status = 'paid'
        return change(who, key, body, 'shared_plan_pay_bill', apply, bill_id=bill_id)

    @app.post('/v2/planning/steps', response_model=PlanningView)
    def add_step(body: AddStep, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            p = require_plan(s)
            old = next((step for step in p.steps if step.id == body.id), None)
            if old:
                if old.amount != body.amount:
                    raise ValueError('This step identity was used with a different amount.')
                return
            facts = planning_view(s, clock())
            if facts.needs_input:
                raise ValueError(facts.needs_input)
            if any(step.status == 'planned' for step in p.steps):
                raise ValueError('Finish or cancel the accepted step first.')
            if p.goal is None or facts.available is None or body.amount > facts.available or body.amount > p.goal.target-p.goal.saved:
                raise ValueError('This step needs a goal and must fit confirmed available money and the remaining target.')
            if len(p.steps) >= 1000:
                raise ValueError('The local step-history limit was reached; existing records were preserved.')
            p.steps.append(Step(id=body.id, account_id=p.account_id, amount=body.amount, created_on=clock()))
            p.deferred = False
        return change(who, key, body, 'shared_plan_accept', apply)

    @app.post('/v2/planning/preview', response_model=PreviewStepView)
    def preview(body: PreviewStep, who=Depends(owner)):
        s = store.read(who)
        facts = planning_view(s, clock())
        p = s.personal.planning
        eligible = (facts.needs_input is None and p.goal is not None and facts.available is not None
                    and not any(step.status == 'planned' for step in p.steps)
                    and body.amount <= facts.available and body.amount <= p.goal.target-p.goal.saved)
        return PreviewStepView(revision=s.revision, amount=body.amount, eligible=eligible,
                               remaining=facts.available-body.amount if facts.available is not None else None,
                               goal_after=p.goal.saved+body.amount if p.goal else None,
                               message='This amount fits your confirmed account plan.' if eligible else facts.needs_input or 'This amount needs a goal, no other accepted step and enough confirmed available money.')

    @app.post('/v2/planning/steps/{step_id}/cancel', response_model=PlanningView)
    def cancel_step(step_id: str, body: PlanningCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            p = require_plan(s)
            step = next((step for step in p.steps if step.id == step_id), None)
            if not step or step.status == 'completed':
                raise ValueError('Only a planned step can be cancelled.')
            step.status = 'cancelled'
        return change(who, key, body, 'shared_plan_cancel', apply, step_id=step_id)

    @app.post('/v2/planning/steps/{step_id}/complete', response_model=PlanningView)
    def complete_step(step_id: str, body: PlanningCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            p = require_plan(s)
            step = next((step for step in p.steps if step.id == step_id), None)
            if not step or step.status == 'cancelled':
                raise ValueError('Only a planned step can be completed.')
            if step.status == 'completed':
                return
            facts = planning_view(s, clock())
            if not facts.can_complete or p.goal is None:
                raise ValueError(facts.needs_input or 'Your available money changed. Review or cancel the step.')
            if p.goal.saved+step.amount > p.goal.target:
                raise ValueError('The step exceeds the remaining goal target.')
            p.goal.saved += step.amount
            step.status, step.completed_on = 'completed', clock()
        return change(who, key, body, 'shared_plan_complete', apply, step_id=step_id)

    @app.post('/v2/planning/defer', response_model=PlanningView)
    def defer(body: PlanningCommand, who=Depends(owner), key=Depends(idempotency)):
        return change(who, key, body, 'shared_plan_defer', lambda s: setattr(require_plan(s), 'deferred', True))

    @app.post('/v2/planning/resume', response_model=PlanningView)
    def resume(body: PlanningCommand, who=Depends(owner), key=Depends(idempotency)):
        return change(who, key, body, 'shared_plan_resume', lambda s: setattr(require_plan(s), 'deferred', False))
