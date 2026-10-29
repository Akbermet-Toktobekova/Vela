"""Local v2 personal-data slice. No statement data or demo defaults become money."""
from datetime import date
from typing import Literal
from uuid import uuid4
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field
from .planning import PlanningState


class PersonalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Account(PersonalRecord):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=60)
    currency: Literal["EUR", "HUF"]
    balance: int | None = Field(default=None, ge=0, le=9_007_199_254_740_991, strict=True)
    confirmed_on: date | None = None


class ReceivedIncome(PersonalRecord):
    id: str
    account_id: str
    amount: int
    received_on: date
    effect: Literal["add", "included", "replace"]


class PersonalState(PersonalRecord):
    planning: PlanningState = Field(default_factory=PlanningState)
    focus: Literal["spending", "reserve", "debt", "goal", "unsure"] = "unsure"
    income_type: Literal["regular", "irregular", "mixed", "unknown"] = "unknown"
    onboarded: bool = False
    accounts: list[Account] = Field(default_factory=list)
    incomes: list[ReceivedIncome] = Field(default_factory=list)


class PersonalView(PersonalRecord):
    revision: int
    data: PersonalState
    mode: Literal["local"] = "local"


class RevisionCommand(PersonalRecord):
    revision: int = Field(ge=0, strict=True)


class ProfileCommand(RevisionCommand):
    focus: Literal["spending", "reserve", "debt", "goal", "unsure"]
    income_type: Literal["regular", "irregular", "mixed", "unknown"]


class AccountCommand(RevisionCommand):
    name: str = Field(min_length=1, max_length=60)
    currency: Literal["EUR", "HUF"]
    balance: int | None = Field(default=None, ge=0, le=9_007_199_254_740_991, strict=True)
    confirmed_on: date


class BalanceCommand(RevisionCommand):
    balance: int = Field(ge=0, le=9_007_199_254_740_991, strict=True)
    confirmed_on: date


class ReceivedCommand(RevisionCommand):
    account_id: str = Field(min_length=1, max_length=80)
    amount: int = Field(gt=0, le=9_007_199_254_740_991, strict=True)
    received_on: date
    effect: Literal["add", "included", "replace"]
    current_balance: int | None = Field(default=None, ge=0, le=9_007_199_254_740_991, strict=True)


def install_personal(app, store, owner, idempotency, clock):
    def render(state):
        return PersonalView(revision=state.revision, data=state.personal).model_dump(mode="json")

    def change(who, key, body, kind, apply):
        return store.mutate(who, key, body.revision,
                            {"kind": kind, **body.model_dump(mode="json")}, apply, render)

    def account(state, account_id):
        result = next((a for a in state.personal.accounts if a.id == account_id), None)
        if result is None:
            raise ValueError("Account not found. Refresh your accounts.")
        return result

    def check_date(value):
        if value > clock():
            raise ValueError("Use a date on or before today.")

    @app.get("/v2/personal", response_model=PersonalView)
    def read(who=Depends(owner)):
        return render(store.read(who))

    @app.put("/v2/profile", response_model=PersonalView)
    def profile(body: ProfileCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(s):
            s.personal.focus = body.focus
            s.personal.income_type = body.income_type
            s.personal.onboarded = True
        return change(who, key, body, "v2_profile", apply)

    @app.post("/v2/accounts", response_model=PersonalView)
    def create_account(body: AccountCommand, who=Depends(owner), key=Depends(idempotency)):
        check_date(body.confirmed_on)
        def apply(s):
            if len(s.personal.accounts) >= 50:
                raise ValueError("You can add up to 50 accounts.")
            s.personal.accounts.append(Account(id=str(uuid4()), name=body.name, currency=body.currency,
                                              balance=body.balance, confirmed_on=body.confirmed_on if body.balance is not None else None))
        return change(who, key, body, "v2_account", apply)

    @app.put("/v2/accounts/{account_id}/balance", response_model=PersonalView)
    def balance(account_id: str, body: BalanceCommand, who=Depends(owner), key=Depends(idempotency)):
        check_date(body.confirmed_on)
        def apply(s):
            a = account(s, account_id)
            a.balance, a.confirmed_on = body.balance, body.confirmed_on
            if s.personal.planning.account_id == a.id:
                s.personal.planning.deferred = False
        return store.mutate(who, key, body.revision,
                            {"kind": "v2_balance", "account_id": account_id, **body.model_dump(mode="json")}, apply, render)

    @app.post("/v2/income", response_model=PersonalView)
    def income(body: ReceivedCommand, who=Depends(owner), key=Depends(idempotency)):
        check_date(body.received_on)
        def apply(s):
            a = account(s, body.account_id)
            if body.effect != "replace" and body.current_balance is not None:
                raise ValueError("Current balance is only used when replacing the balance.")
            if body.effect == "add":
                if a.balance is None:
                    raise ValueError("Your balance is unknown. Enter your current balance instead.")
                if a.confirmed_on and body.received_on < a.confirmed_on:
                    raise ValueError("This income predates your balance. Record it as already included or enter a current balance.")
                if a.balance + body.amount > 9_007_199_254_740_991:
                    raise ValueError("This balance is too large.")
                a.balance += body.amount
                a.confirmed_on = body.received_on
            elif body.effect == "replace":
                if body.current_balance is None:
                    raise ValueError("Enter your current balance.")
                a.balance, a.confirmed_on = body.current_balance, clock()
            s.personal.incomes.append(ReceivedIncome(id=str(uuid4()), account_id=a.id, amount=body.amount,
                                                    received_on=body.received_on, effect=body.effect))
            if s.personal.planning.account_id == a.id and body.effect != 'included':
                s.personal.planning.deferred = False
        return change(who, key, body, "v2_income", apply)
