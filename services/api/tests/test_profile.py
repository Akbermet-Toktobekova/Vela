"""Synthetic persisted profile proofs; expectations/preferences are never money."""
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
import unittest

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import select

from vela.domain import State
from vela.personal import install_personal
from vela.profile import install_profile
from vela.store import Conflict, Store, states, receipts


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.url = f'sqlite:///{Path(self.temp.name)/"synthetic-profile.db"}'
        self.day = date(2026, 10, 29)
        self.make_app()

    def make_app(self):
        self.store = Store(self.url)
        self.app = FastAPI()
        def owner(authorization: Annotated[str | None, Header()] = None):
            owners = {'Bearer profile-A': 'A', 'Bearer profile-B': 'B'}
            if authorization not in owners:
                raise HTTPException(401, 'Synthetic owner credentials required.')
            return owners[authorization]
        def key(idempotency_key: Annotated[str, Header(min_length=8, max_length=100)]):
            return idempotency_key
        @self.app.exception_handler(Conflict)
        async def conflict(request, exc):
            return JSONResponse({'detail': str(exc)}, status_code=409)
        @self.app.exception_handler(ValueError)
        async def invalid(request, exc):
            return JSONResponse({'detail': str(exc)}, status_code=422)
        install_personal(self.app, self.store, owner, key, lambda: self.day)
        install_profile(self.app, self.store, owner, key, lambda: self.day)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.store.engine.dispose()
        self.temp.cleanup()

    def get(self, owner='A'):
        return self.client.get('/v2/profile/details', headers={'Authorization': 'Bearer profile-'+owner})

    def put(self, path, body, key='profile-command-1', owner='A'):
        return self.client.put('/v2/profile/'+path, json=body, headers={
            'Authorization': 'Bearer profile-'+owner, 'Idempotency-Key': key})

    def fact(self, confirmed=True):
        return {'source': 'manual', 'source_date': '2026-10-25', 'confirmed': confirmed}

    def command(self, **changes):
        return {'revision': 0, 'preference_version': 0, 'income_input_version': 0,
                'fact': self.fact(), **changes}

    def rows(self):
        with self.store.engine.connect() as conn:
            return (conn.execute(select(states)).fetchall(), conn.execute(select(receipts)).fetchall())

    def test_empty_profile_is_optional_unknown_and_read_creates_no_record(self):
        data = self.get().json()
        self.assertEqual((data['revision'], data['focus'], data['income_type']), (0, 'unsure', 'unknown'))
        self.assertIsNone(data['details']['income_estimate'])
        self.assertIsNone(data['details']['preferences'])
        self.assertIsNone(data['details']['onboarding'])
        self.assertIsNone(data['freshness']['income_estimate']['confirmed_on'])
        self.assertEqual(self.rows(), ([], []))
        self.assertEqual(self.client.get('/v2/profile/details').status_code, 401)

    def test_persistence_versions_fact_dates_and_separate_preferences_after_restart(self):
        result = self.put('details', self.command(focus='reserve', income_type='mixed', income_estimate={
            'minimum_minor': 100000, 'maximum_minor': 180000, 'currency': 'EUR',
            'frequency': 'monthly', 'next_expected_on': '2026-11-15'}))
        self.assertEqual(result.status_code, 200, result.text)
        data = result.json()
        self.assertEqual((data['revision'], data['details']['preference_version'], data['details']['income_input_version']), (1, 1, 1))
        self.assertEqual(data['freshness']['income_estimate'], {'source': 'manual', 'source_date': '2026-10-25',
            'recorded_on': '2026-10-29', 'confirmed_on': '2026-10-29', 'age_days': 4})
        result = self.put('preferences', {'revision': 1, 'preference_version': 1, 'preferences': {
            'preferences': ['Prefer a small number of choices'], 'restrictions': ['No new borrowing']}, 'fact': self.fact()}, 'preferences-command')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual((result.json()['details']['preference_version'], result.json()['details']['income_input_version']), (2, 1))
        before = result.json()
        self.client.close(); self.store.engine.dispose(); self.make_app()
        self.assertEqual(self.get().json(), before)

    def test_income_expectation_and_explicit_unknown_do_not_change_received_money(self):
        account = self.client.post('/v2/accounts', json={'revision': 0, 'name': 'Synthetic', 'currency': 'EUR',
            'balance': 50000, 'confirmed_on': '2026-10-29'}, headers={'Authorization': 'Bearer profile-A', 'Idempotency-Key': 'account-fixture'}).json()
        before = self.store.read('A').personal.accounts[0].model_dump()
        result = self.put('details', self.command(revision=1, income_estimate={
            'amount_minor': 100000, 'currency': 'HUF', 'next_expected_on': '2026-12-01'}))
        self.assertEqual(result.status_code, 200, result.text)
        state = self.store.read('A')
        self.assertEqual(state.personal.accounts[0].model_dump(), before)
        self.assertEqual(state.personal.incomes, [])
        self.assertIsNone(state.snapshot)
        result = self.put('details', self.command(revision=2, income_input_version=1, income_estimate=None), 'clear-income-command')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertIsNone(result.json()['details']['income_estimate'])
        self.assertEqual(self.store.read('A').personal.accounts[0].balance, 50000)
        self.assertEqual(self.store.read('A').personal.incomes, [])

    def test_owner_isolation_and_spoof_rejected_without_side_effects(self):
        body = self.command(focus='goal')
        self.assertEqual(self.put('details', body).status_code, 200)
        self.assertEqual(self.get('B').json()['focus'], 'unsure')
        self.assertEqual(self.put('details', {**body, 'user_id': 'A'}, owner='B').status_code, 422)
        self.assertEqual(self.get('B').json()['revision'], 0)
        self.assertEqual(self.put('details', self.command(focus='debt'), owner='B').status_code, 200)
        self.assertEqual(self.get().json()['focus'], 'goal')
        self.assertEqual(self.get('B').json()['focus'], 'debt')

    def test_exact_retry_changed_body_and_stale_versions_are_atomic(self):
        body = self.command(focus='reserve')
        first = self.put('details', body)
        self.assertEqual(first.status_code, 200)
        rows = self.rows()
        self.assertEqual(self.put('details', body).json(), first.json())
        self.assertEqual(self.rows(), rows)
        self.assertEqual(self.put('details', {**body, 'focus': 'goal'}).status_code, 409)
        self.assertEqual(self.put('details', body, 'new-stale-revision').status_code, 409)
        self.assertEqual(self.put('details', self.command(revision=1, focus='goal'), 'stale-preference').status_code, 409)
        self.assertEqual(self.put('preferences', {'revision': 1, 'preference_version': 0, 'preferences': None, 'fact': self.fact()}, 'stale-preferences').status_code, 409)
        self.assertEqual(self.rows(), rows)

    def test_invalid_ranges_precision_currency_and_missing_change_never_write(self):
        variants = [{'minimum_minor': 2}, {'minimum_minor': 3, 'maximum_minor': 2, 'currency': 'EUR'},
            {'amount_minor': 10, 'minimum_minor': 1, 'maximum_minor': 20, 'currency': 'EUR'},
            {'amount_minor': -1, 'currency': 'EUR'}, {'amount_minor': 1.5, 'currency': 'EUR'},
            {'amount_minor': True, 'currency': 'EUR'}, {'amount_minor': 10}, {'amount_minor': 10, 'currency': 'USD'},
            {'amount_minor': 9_007_199_254_740_992, 'currency': 'EUR'}, {'frequency': ' '}]
        for estimate in variants:
            with self.subTest(estimate=estimate):
                self.assertEqual(self.put('details', self.command(income_estimate=estimate)).status_code, 422)
                self.assertEqual(self.rows(), ([], []))
        self.assertEqual(self.put('details', self.command()).status_code, 422)
        self.assertEqual(self.put('preferences', {'revision': 0, 'preference_version': 0, 'preferences': {'restrictions': [' ']}, 'fact': self.fact()}).status_code, 422)
        self.assertEqual(self.rows(), ([], []))

    def test_future_fact_rejected_but_explicit_zero_is_not_unknown(self):
        body = self.command(income_estimate={'amount_minor': 0, 'currency': 'EUR'})
        body['fact']['source_date'] = '2026-10-30'
        self.assertEqual(self.put('details', body).status_code, 422)
        self.assertEqual(self.rows(), ([], []))
        body['fact'] = self.fact(False)
        data = self.put('details', body).json()
        self.assertEqual(data['details']['income_estimate']['amount_minor'], 0)
        self.assertIsNone(data['freshness']['income_estimate']['confirmed_on'])
        self.assertEqual(self.store.read('A').personal.incomes, [])

    def test_legacy_markers_have_no_invented_confirmation_and_old_new_old_stays_consistent(self):
        legacy = {'revision': 0, 'focus': 'goal', 'income_type': 'regular'}
        self.assertEqual(self.put('', legacy, 'legacy-profile-1').status_code, 200)
        data = self.get().json()
        self.assertEqual(data['freshness']['focus']['source'], 'legacy')
        self.assertEqual(data['details']['focus_fact']['source'], 'legacy')
        self.assertIsNone(data['freshness']['focus']['confirmed_on'])
        confirmed = self.put('details', self.command(revision=1, focus='goal', income_type='regular'), 'confirm-profile').json()
        self.assertEqual(confirmed['details']['preference_version'], 1)
        self.assertEqual(confirmed['details']['income_input_version'], 1)
        changed = self.put('', {'revision': 2, 'focus': 'reserve', 'income_type': 'irregular'}, 'legacy-profile-2')
        self.assertEqual(changed.status_code, 200, changed.text)
        data = self.get().json()
        self.assertEqual((data['focus'], data['income_type']), ('reserve', 'irregular'))
        self.assertEqual((data['details']['preference_version'], data['details']['income_input_version']), (2, 2))
        self.assertIsNone(data['freshness']['focus']['confirmed_on'])
        self.assertIsNone(data['freshness']['income_type']['confirmed_on'])

    def test_onboarding_can_skip_resume_and_complete_without_financial_defaults(self):
        body = {'revision': 0, 'step': 'income', 'skipped': ['accounts']}
        result = self.put('onboarding', body, 'onboarding-command')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['details']['onboarding'], {'step': 'income', 'skipped': ['accounts'], 'updated_on': '2026-10-29'})
        self.assertEqual(self.put('onboarding', body, 'onboarding-command').json(), result.json())
        self.assertEqual(result.json()['details']['preference_version'], 0)
        self.assertEqual(result.json()['details']['income_input_version'], 0)
        self.client.close(); self.store.engine.dispose(); self.make_app()
        self.assertEqual(self.get().json()['details']['onboarding']['step'], 'income')
        result = self.put('onboarding', {'revision': 1, 'step': 'complete'}, 'onboarding-complete')
        self.assertEqual(result.status_code, 200)
        state = self.store.read('A')
        self.assertTrue(state.personal.onboarded)
        self.assertEqual(state.personal.accounts, [])
        self.assertEqual(state.personal.incomes, [])
        self.assertIsNone(state.snapshot)
        self.assertFalse(state.personal.planning.active)

    def test_legacy_raw_payload_read_is_opaque_and_profile_write_preserves_financial_facts(self):
        legacy = State().model_dump(mode='json')
        legacy['personal'].pop('profile_details')
        legacy['history'] = [{'event': 'synthetic-legacy', 'revision': 4}]
        legacy['revision'] = 4
        legacy['transactions'] = [{'id': 'original', 'date': '2026-08-02', 'description': 'SYNTHETIC refund', 'amount': 2000, 'category': 'refunds', 'source': 'import:original'}]
        legacy['personal']['accounts'] = [{'id': 'account', 'name': 'Legacy Á', 'currency': 'HUF', 'balance': None, 'confirmed_on': None}]
        raw = json.dumps(legacy, indent=3, ensure_ascii=False)
        with self.store.engine.begin() as conn:
            conn.execute(states.insert().values(owner='A', revision=4, payload=raw))
        before = self.rows()
        self.assertEqual(self.get().status_code, 200)
        self.assertEqual(self.rows(), before)
        self.client.close(); self.store.engine.dispose(); self.make_app()
        self.assertEqual(self.rows(), before)
        data = self.put('details', self.command(revision=4, focus='spending'), 'expand-profile')
        self.assertEqual(data.status_code, 200, data.text)
        current = self.store.read('A').model_dump(mode='json')
        for field in ('transactions', 'snapshot', 'actions', 'debts', 'income_ids', 'deferred'):
            self.assertEqual(current[field], legacy[field])
        self.assertEqual(current['history'][:1], legacy['history'])
        self.assertEqual(current['personal']['accounts'], legacy['personal']['accounts'])
        self.assertEqual(current['personal']['incomes'], legacy['personal']['incomes'])
