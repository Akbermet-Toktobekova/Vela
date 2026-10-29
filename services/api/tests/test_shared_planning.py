import json
import sqlite3
import unittest
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from vela.main import create_app
from vela.domain import State


class SharedPlanningTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.db = self.path/'plan.db'
        self.day = date(2026, 10, 29)
        self.token = 'shared-account-plan-test-token-0001'
        self.app = create_app(f'sqlite:///{self.db}', self.token, today=lambda: self.day, local_dir=self.path)
        self.client = TestClient(self.app)
        self.headers = {'Authorization': 'Bearer '+self.token}
        self.count = 0

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        self.temp.cleanup()

    def get(self, route='/v2/planning'):
        r = self.client.get(route, headers=self.headers)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def command(self, route, body, method='POST', key=None):
        self.count += 1
        return self.client.request(method, route, json=body, headers={**self.headers, 'Idempotency-Key': key or f'shared-test-{self.count:04}'})

    def write(self, route, body=None, method='POST', key=None):
        body = {'revision': self.get()['revision'], **(body or {})}
        r = self.command(route, body, method, key)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def account(self, balance=100000, currency='EUR'):
        data = self.write('/v2/accounts', {'name': 'Main', 'currency': currency, 'balance': balance, 'confirmed_on': str(self.day)})
        return data['data']['accounts'][-1]['id']

    def config(self, account_id, goal=True, **updates):
        return self.write('/v2/planning', {'account_id': account_id, 'horizon': str(self.day+timedelta(days=30)),
                         'protected': 10000, 'bills_confirmed': True, 'debts_confirmed': True,
                         'goal': {'name': 'Reserve', 'target': 100000} if goal else None, **updates}, 'PUT')

    def p0(self):
        account = self.account()
        self.config(account)
        for i, (amount, days) in enumerate([(60000, 7), (15000, 14), (5000, 21)]):
            self.write('/v2/planning/bills', {'id': f'bill-{i}', 'label': f'Bill{i}', 'amount': amount, 'currency': 'EUR', 'due': str(self.day+timedelta(days=days))})
        self.assertEqual(self.get()['available'], 10000)
        return account

    def test_canonical_income_reserve_complete_restart_and_lower_actual_balance(self):
        account = self.p0()
        plan = self.write('/v2/planning/steps', {'id': 'step-1', 'amount': 4000})
        self.assertEqual((plan['cash'], plan['reserved'], plan['available'], plan['goal_saved']), (100000, 4000, 6000, 0))
        self.write('/v2/income', {'account_id': account, 'amount': 10000, 'received_on': str(self.day), 'effect': 'add'})
        self.assertEqual(self.get()['cash'], 110000)
        self.assertEqual(self.get()['available'], 16000)
        body = {'revision': self.get()['revision']}
        first = self.command('/v2/planning/steps/step-1/complete', body, key='complete-one-time')
        retry = self.command('/v2/planning/steps/step-1/complete', body, key='complete-one-time')
        self.assertEqual(first.json(), retry.json())
        self.assertEqual((first.json()['cash'], first.json()['available'], first.json()['goal_saved']), (110000, 16000, 4000))
        self.assertEqual(self.get('/v2/personal')['data']['accounts'][0]['balance'], 110000)
        self.assertIsNone(self.get('/v1/export')['snapshot'])
        restarted = create_app(f'sqlite:///{self.db}', self.token, today=lambda: self.day, local_dir=self.path)
        try:
            with TestClient(restarted) as c:
                self.assertEqual(c.get('/v2/planning', headers=self.headers).json()['goal_saved'], 4000)
        finally:
            restarted.state.store.engine.dispose()
        self.write(f'/v2/accounts/{account}/balance', {'balance': 2000, 'confirmed_on': str(self.day)}, 'PUT')
        facts = self.get()
        self.assertEqual(facts['cash'], 2000)
        self.assertEqual(facts['goal_saved'], 4000)
        self.assertEqual(facts['recommendation_kind'], 'shortfall')
        self.assertFalse(facts['can_complete'])

    def test_shortfall_cancel_freshness_and_bill_payment_modes(self):
        account = self.p0()
        self.write('/v2/planning/steps', {'id': 'step-1', 'amount': 4000})
        self.write('/v2/planning/bills', {'id': 'extra', 'label': 'Extra', 'amount': 8000, 'currency': 'EUR', 'due': str(self.day)})
        self.assertEqual(self.get()['available'], -2000)
        self.assertFalse(self.get()['can_complete'])
        bad = self.command('/v2/planning/steps/step-1/complete', {'revision': self.get()['revision']})
        self.assertEqual(bad.status_code, 422)
        self.write('/v2/planning/steps/step-1/cancel')
        self.assertEqual(self.get()['available'], 2000)
        self.write('/v2/planning/bills/extra/cancel')
        self.assertEqual(self.get()['cash'], 100000)
        self.write('/v2/planning/bills', {'id': 'pay', 'label': 'Pay', 'amount': 8000, 'currency': 'EUR', 'due': str(self.day)})
        body = {'revision': self.get()['revision'], 'effect': 'subtract'}
        paid = self.command('/v2/planning/bills/pay/pay', body, key='paid-one-time')
        retry = self.command('/v2/planning/bills/pay/pay', body, key='paid-one-time')
        self.assertEqual(paid.json(), retry.json())
        self.assertEqual(self.get()['cash'], 92000)
        self.assertEqual(self.get('/v2/personal')['data']['accounts'][0]['balance'], 92000)
        self.write('/v2/planning/bills', {'id': 'included', 'label': 'Already reflected', 'amount': 1000, 'currency': 'EUR', 'due': str(self.day)})
        self.write('/v2/planning/bills/included/pay', {'effect': 'already_in_balance'})
        self.assertEqual(self.get()['cash'], 92000)
        self.day += timedelta(days=1)
        self.assertIsNotNone(self.get()['needs_input'])
        self.assertEqual(self.command('/v2/planning/steps', {'revision': self.get()['revision'], 'id': 'stale', 'amount': 500}).status_code, 422)
        self.write(f'/v2/accounts/{account}/balance', {'balance': 92000, 'confirmed_on': str(self.day)}, 'PUT')
        self.assertIsNone(self.get()['needs_input'])

    def test_optional_goal_unknown_inputs_huf_and_stale_commands(self):
        account = self.account(balance=None)
        self.config(account, goal=False, protected=None, bills_confirmed=False)
        self.assertIsNone(self.get()['cash'])
        self.assertIsNone(self.get()['available'])
        self.assertIsNone(self.get()['planning']['goal'])
        self.write(f'/v2/accounts/{account}/balance', {'balance': 100000, 'confirmed_on': str(self.day)}, 'PUT')
        self.config(account, goal=False)
        self.assertEqual(self.get()['recommendation_kind'], 'maintain')
        self.assertEqual(self.get()['available'], 90000)
        old_revision = self.get()['revision']
        self.write('/v2/planning/defer')
        self.assertEqual(self.command('/v2/planning/defer', {'revision': old_revision}).status_code, 409)
        huf = self.account(currency='HUF')
        bad = self.command('/v2/planning', {'revision': self.get()['revision'], 'account_id': huf, 'horizon': str(self.day+timedelta(days=30)),
                                           'protected': 0, 'bills_confirmed': True, 'debts_confirmed': True}, 'PUT')
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(self.get()['planning']['account_id'], account)
        self.assertEqual(self.client.get('/v2/planning').status_code, 401)

    def test_explicit_legacy_adoption_preserves_old_records_and_blocks_old_cash_writes(self):
        self.write('/v1/demo')
        account = self.account()
        step = self.write('/v1/actions', {'amount': 2000})['actions'][0]['id']
        self.write(f'/v1/actions/{step}/complete')
        before = self.get('/v1/export')
        # A restorable SQLite copy is made before expansion; live data is never erased.
        backup = self.path/'before-adoption.db'
        with closing(sqlite3.connect(self.db)) as original, closing(sqlite3.connect(backup)) as copy:
            original.backup(copy)
        adopted = self.write('/v2/planning/adopt-legacy', {'account_id': account, 'confirm_finances': True}, key='adopt-once')
        self.assertEqual(adopted['goal_saved'], 2000)
        after = self.get('/v1/export')
        for field in ('snapshot', 'actions', 'debts', 'transactions'):
            self.assertEqual(after[field], before[field], field)
        self.assertEqual(self.command('/v1/actions', {'revision': after['revision'], 'amount': 500}).status_code, 422)
        self.assertEqual(self.command('/v1/snapshot', {'revision': after['revision'], 'snapshot': before['snapshot']}, 'PUT').status_code, 422)
        with closing(sqlite3.connect(backup)) as restored:
            payload = restored.execute('SELECT payload FROM demo_state').fetchone()[0]
        self.assertFalse(State.model_validate_json(payload).personal.planning.active)
        self.assertEqual(json.loads(payload)['actions'], before['actions'])
        old_shape = before.copy()
        old_shape['personal'].pop('planning')
        self.assertFalse(State.model_validate(old_shape).personal.planning.active)

    def test_shared_readers_never_use_preserved_legacy_snapshot(self):
        self.write('/v1/demo')
        account = self.account()
        self.write('/v2/planning/adopt-legacy', {'account_id': account, 'confirm_finances': True})
        before = self.get('/v1/export')['snapshot']
        self.write(f'/v2/accounts/{account}/balance', {'balance': 1000, 'confirmed_on': str(self.day)}, 'PUT')
        lessons = self.get('/v1/lessons')
        self.assertEqual(lessons['active_recommendation_kind'], 'shortfall')
        self.assertEqual(lessons['active_action_id'], 'external_assistance_shortfall')
        state = self.get('/v1/state')
        self.assertIsNone(state['snapshot'])
        self.assertEqual(state['actions'], [])
        self.assertEqual(state['recommendation']['kind'], 'clarify')
        self.assertEqual(self.get('/v1/export')['snapshot'], before)
        revision = self.get()['revision']
        self.assertEqual(self.client.get('/v1/decision', headers=self.headers).status_code, 409)
        for route, body in [('/v1/decision/evaluate', {'revision': revision}),
                            ('/v1/preview', {'amount': 100}),
                            ('/v1/chat', {'messages': [{'role': 'user', 'content': 'Explain my next step'}]})]:
            response = self.command(route, body)
            self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(self.get()['revision'], revision)

    def test_empty_lessons_adoption_mismatch_and_debt_confirmation(self):
        self.assertGreater(self.get('/v1/lessons')['total_count'], 0)
        self.write('/v1/demo')
        account = self.account(balance=99900)
        before = self.get('/v1/export')
        response = self.command('/v2/planning/adopt-legacy', {'revision': before['revision'], 'account_id': account, 'confirm_finances': True})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.get('/v1/export'), before)
        self.write(f'/v2/accounts/{account}/balance', {'balance': 100000, 'confirmed_on': str(self.day)}, 'PUT')
        self.write('/v2/planning/adopt-legacy', {'account_id': account, 'confirm_finances': True})
        self.write('/v1/debts', {'debt': {'id': 'debt-new', 'balance_cents': 10000, 'apr_bps': 1000}})
        self.assertFalse(self.get()['planning']['debts_confirmed'])
        self.assertIsNotNone(self.get()['needs_input'])


    def test_shared_plan_imports_remain_analytical_and_deduplicate(self):
        self.p0()
        before = self.get('/v1/export')
        fixtures = Path(__file__).resolve().parents[3] / 'docs/testing/pattern-statements'
        for month in ('07', '08', '09', '09'):
            file = fixtures / f'SYNTHETIC-2026-{month}-EUR.csv'
            response = self.client.post('/v1/imports', headers=self.headers, files={'file': (file.name, file.read_bytes(), 'text/csv')})
            self.assertEqual(response.status_code, 200, response.text)
            self.write(f"/v2/imports/{response.json()['id']}/apply")
        after = self.get('/v1/export')
        self.assertEqual(len(after['transactions']), 56)
        self.assertEqual(after['personal'], before['personal'])
        self.assertEqual(after['snapshot'], before['snapshot'])
        self.assertEqual(after['actions'], before['actions'])
