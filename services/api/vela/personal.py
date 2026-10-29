"""Local v2 personal-data slice. No statement data or demo defaults become money."""
from datetime import date
from typing import Literal
from uuid import uuid4
from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, model_validator
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


class ProfileFact(PersonalRecord):
    source: Literal["unknown", "legacy", "manual"] = "unknown"
    source_date: date | None = None
    recorded_on: date | None = None
    confirmed_on: date | None = None


class IncomeEstimate(PersonalRecord):
    """Stated expectation only: it is never a ReceivedIncome or balance effect."""
    amount_minor: int | None = Field(default=None, ge=0, le=9_007_199_254_740_991, strict=True)
    minimum_minor: int | None = Field(default=None, ge=0, le=9_007_199_254_740_991, strict=True)
    maximum_minor: int | None = Field(default=None, ge=0, le=9_007_199_254_740_991, strict=True)
    currency: Literal["EUR", "HUF"] | None = None
    frequency: str | None = Field(default=None, min_length=1, max_length=80)
    next_expected_on: date | None = None

    @model_validator(mode="after")
    def consistent_amount(self):
        if self.frequency is not None and not self.frequency.strip():
            raise ValueError("Enter a frequency label or leave it unknown.")
        ranged = self.minimum_minor is not None or self.maximum_minor is not None
        if ranged and (self.minimum_minor is None or self.maximum_minor is None):
            raise ValueError("Enter both ends of an income range, or leave both unknown.")
        if self.amount_minor is not None and ranged:
            raise ValueError("Choose an approximate amount or a range, not both.")
        if ranged and self.minimum_minor > self.maximum_minor:
            raise ValueError("The minimum income cannot exceed the maximum.")
        if (ranged or self.amount_minor is not None) and self.currency is None:
            raise ValueError("Choose a currency for the expected income amount.")
        return self


class ProfilePreferences(PersonalRecord):
    # Explicit user text only. No weights, inferred motives or financial rules.
    preferences: list[str] = Field(default_factory=list, max_length=30)
    restrictions: list[str] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def bounded_text(self):
        for values in (self.preferences, self.restrictions):
            if any(not value.strip() or len(value) > 200 for value in values):
                raise ValueError("Use nonempty preference or restriction text up to 200 characters.")
            if len(set(values)) != len(values):
                raise ValueError("Do not repeat the same preference or restriction.")
        return self


OnboardingStep = Literal["focus", "accounts", "income", "obligations", "complete"]


class ProfileOnboarding(PersonalRecord):
    step: OnboardingStep
    skipped: list[Literal["focus", "accounts", "income", "obligations"]] = Field(default_factory=list, max_length=4)
    updated_on: date


class ProfileDetails(PersonalRecord):
    preference_version: int = Field(default=0, ge=0, strict=True)
    income_input_version: int = Field(default=0, ge=0, strict=True)
    income_estimate: IncomeEstimate | None = None
    preferences: ProfilePreferences | None = None
    onboarding: ProfileOnboarding | None = None
    focus_fact: ProfileFact = Field(default_factory=ProfileFact)
    income_type_fact: ProfileFact = Field(default_factory=ProfileFact)
    income_estimate_fact: ProfileFact = Field(default_factory=ProfileFact)
    preferences_fact: ProfileFact = Field(default_factory=ProfileFact)


class PersonalState(PersonalRecord):
    planning: PlanningState = Field(default_factory=PlanningState)
    profile_details: ProfileDetails | None = None
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
            # Legacy command remains compatible, but cannot retain contradictory
            # confirmation/version evidence after changing the profile markers.
            details = s.personal.profile_details
            if details is not None:
                fact = ProfileFact(source="manual", source_date=clock(), recorded_on=clock())
                if s.personal.focus != body.focus:
                    details.preference_version += 1
                    details.focus_fact = fact.model_copy()
                if s.personal.income_type != body.income_type:
                    details.income_input_version += 1
                    details.income_type_fact = fact.model_copy()
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
