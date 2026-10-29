"""Optional owner profile facts/preferences; expectations never create cash."""
from datetime import date
from typing import Literal

from fastapi import Depends
from pydantic import Field, model_validator

from .personal import (IncomeEstimate, OnboardingStep, PersonalRecord, ProfileDetails,
                       ProfileFact, ProfileOnboarding, ProfilePreferences, RevisionCommand)
from .store import Conflict


class ManualProfileFact(PersonalRecord):
    source: Literal['manual'] = 'manual'
    source_date: date
    confirmed: bool = Field(strict=True)


class ProfileDetailsCommand(RevisionCommand):
    preference_version: int = Field(ge=0, strict=True)
    income_input_version: int = Field(ge=0, strict=True)
    focus: Literal['spending', 'reserve', 'debt', 'goal', 'unsure'] | None = None
    income_type: Literal['regular', 'irregular', 'mixed', 'unknown'] | None = None
    income_estimate: IncomeEstimate | None = None
    fact: ManualProfileFact

    @model_validator(mode='after')
    def has_change(self):
        if not self.model_fields_set.intersection({'focus', 'income_type', 'income_estimate'}):
            raise ValueError('Choose a profile field to update or explicitly clear.')
        return self


class PreferencesCommand(RevisionCommand):
    preference_version: int = Field(ge=0, strict=True)
    preferences: ProfilePreferences | None
    fact: ManualProfileFact


class OnboardingCommand(RevisionCommand):
    step: OnboardingStep
    skipped: list[Literal['focus', 'accounts', 'income', 'obligations']] = Field(default_factory=list, max_length=4)

    @model_validator(mode='after')
    def unique_steps(self):
        if len(set(self.skipped)) != len(self.skipped):
            raise ValueError('List each skipped step only once.')
        return self


class FactFreshness(PersonalRecord):
    source: Literal['unknown', 'legacy', 'manual']
    source_date: date | None
    recorded_on: date | None
    confirmed_on: date | None
    age_days: int | None


class ProfileDetailsView(PersonalRecord):
    revision: int
    focus: Literal['spending', 'reserve', 'debt', 'goal', 'unsure']
    income_type: Literal['regular', 'irregular', 'mixed', 'unknown']
    details: ProfileDetails
    freshness: dict[str, FactFreshness]
    as_of: date


def install_profile(app, store, owner, idempotency, clock):
    def render(state):
        details = (state.personal.profile_details or ProfileDetails()).model_copy(deep=True)
        freshness = {}
        for name in ('focus', 'income_type', 'income_estimate', 'preferences'):
            fact = getattr(details, name+'_fact')
            source = fact.source
            # Old selectors are visible, but no retrospective confirmation/date.
            if source == 'unknown' and name in ('focus', 'income_type') and getattr(state.personal, name) not in ('unsure', 'unknown'):
                source = 'legacy'
                fact.source = source
            freshness[name] = FactFreshness(source=source, source_date=fact.source_date,
                recorded_on=fact.recorded_on, confirmed_on=fact.confirmed_on,
                age_days=(clock()-fact.source_date).days if fact.source_date else None)
        return ProfileDetailsView(revision=state.revision, focus=state.personal.focus,
            income_type=state.personal.income_type, details=details, freshness=freshness,
            as_of=clock()).model_dump(mode='json')

    def fact(body):
        if body.source_date > clock():
            raise ValueError('A profile fact source date cannot be in the future.')
        return ProfileFact(source='manual', source_date=body.source_date, recorded_on=clock(),
                           confirmed_on=clock() if body.confirmed else None)

    def details(state):
        if state.personal.profile_details is None:
            state.personal.profile_details = ProfileDetails()
        return state.personal.profile_details

    def mutate(who, key, body, kind, apply):
        return store.mutate(who, key, body.revision, {'kind': kind, **body.model_dump(mode='json', exclude_unset=True)}, apply, render)

    @app.get('/v2/profile/details', response_model=ProfileDetailsView)
    def get_profile(who=Depends(owner)):
        return render(store.read(who))

    @app.put('/v2/profile/details', response_model=ProfileDetailsView)
    def update_profile(body: ProfileDetailsCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(state):
            values = details(state)
            if values.preference_version != body.preference_version or values.income_input_version != body.income_input_version:
                raise Conflict('Your profile changed. Refresh and try again.')
            evidence = fact(body.fact)
            preference_changed = income_changed = False
            if 'focus' in body.model_fields_set:
                focus = body.focus or 'unsure'
                preference_changed = state.personal.focus != focus or values.focus_fact != evidence
                state.personal.focus, values.focus_fact = focus, evidence.model_copy()
            if 'income_type' in body.model_fields_set:
                income_type = body.income_type or 'unknown'
                income_changed = state.personal.income_type != income_type or values.income_type_fact != evidence
                state.personal.income_type, values.income_type_fact = income_type, evidence.model_copy()
            if 'income_estimate' in body.model_fields_set:
                income_changed = income_changed or values.income_estimate != body.income_estimate or values.income_estimate_fact != evidence
                values.income_estimate, values.income_estimate_fact = body.income_estimate, evidence.model_copy()
            values.preference_version += int(preference_changed)
            values.income_input_version += int(income_changed)
        return mutate(who, key, body, 'v2_profile_details', apply)

    @app.put('/v2/profile/preferences', response_model=ProfileDetailsView)
    def update_preferences(body: PreferencesCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(state):
            values = details(state)
            if values.preference_version != body.preference_version:
                raise Conflict('Your preferences changed. Refresh and try again.')
            evidence = fact(body.fact)
            if values.preferences != body.preferences or values.preferences_fact != evidence:
                values.preference_version += 1
            values.preferences, values.preferences_fact = body.preferences, evidence
        return mutate(who, key, body, 'v2_profile_preferences', apply)

    @app.put('/v2/profile/onboarding', response_model=ProfileDetailsView)
    def update_onboarding(body: OnboardingCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(state):
            details(state).onboarding = ProfileOnboarding(step=body.step, skipped=body.skipped, updated_on=clock())
            state.personal.onboarded = body.step == 'complete'
        return mutate(who, key, body, 'v2_profile_onboarding', apply)

