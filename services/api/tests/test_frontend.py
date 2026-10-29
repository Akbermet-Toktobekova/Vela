import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from vela.main import create_app


class FrontendTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.db = f'sqlite:///{self.folder / "synthetic.db"}'
        self.day = date(2026, 10, 29)
        self.token = 'frontend-isolated-test-token-0001'
        self.origin = 'http://localhost:5173'
        self.app = create_app(self.db, self.token, today=lambda: self.day, local_dir=self.folder, frontend_origins=[self.origin])
        self.client = TestClient(self.app)
        self.auth = {'Authorization': 'Bearer ' + self.token}
        self.count = 0

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        self.temp.cleanup()

    def get(self, path='/v2/frontend'):
        response = self.client.get(path, headers=self.auth)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def write(self, path, body=None, method='POST', key=None, status=200):
        self.count += 1
        data = {'revision': self.get()['revision'], **(body or {})}
        response = self.client.request(method, path, headers={**self.auth, 'Idempotency-Key': key or f'frontend-test-{self.count:04}'}, json=data)
        self.assertEqual(response.status_code, status, response.text)
        return response.json()

    def setup_plan(self, goal=True, balance=100000):
        personal = self.write('/v2/accounts', {'name': 'Synthetic', 'currency': 'EUR', 'balance': balance, 'confirmed_on': str(self.day)})
        account = personal['data']['accounts'][0]['id']
        self.write('/v2/planning', {'account_id': account, 'horizon': str(self.day+timedelta(days=30)),
            'protected': 10000, 'bills_confirmed': True, 'debts_confirmed': True,
            'goal': {'name': 'Example', 'target': 100000} if goal else None}, method='PUT')
        self.write('/v2/planning/bills', {'id': 'essentials', 'label': 'Essentials', 'amount': 80000, 'currency': 'EUR', 'due': str(self.day+timedelta(days=7))})
        return account

    def test_empty_unknown_no_goal_and_capabilities(self):
        empty = self.get()
        self.assertEqual(empty['revision'], 0)
        self.assertIsNone(empty['assistant']['plan']['cash'])
        self.assertIsNone(empty['assistant']['plan']['available'])
        self.assertEqual(empty['assistant']['plan']['recommendation_kind'], 'clarify')
        for name in ['cloud_otp', 'multi_user', 'persistent_chat', 'bank_connections', 'money_transfers', 'server_reminders', 'multi_goal', 'fx_in_plan']:
            self.assertFalse(empty['capabilities'][name])
        account = self.setup_plan(goal=False, balance=None)
        self.assertIsNone(self.get()['assistant']['plan']['cash'])
        self.write(f'/v2/accounts/{account}/balance', {'balance': 100000, 'confirmed_on': str(self.day)}, method='PUT')
        view = self.get()
        self.assertEqual(view['assistant']['plan']['available'], 10000)
        self.assertEqual(view['assistant']['plan']['recommendation_kind'], 'maintain')
        self.write('/v2/planning/steps', {'id': 'no-goal', 'amount': 4000}, status=422)

    def test_same_revision_money_sequence_and_restart(self):
        account = self.setup_plan()
        self.write('/v2/planning/steps', {'id': 'step-40', 'amount': 4000})
        self.assertEqual(self.get()['assistant']['plan']['available'], 6000)
        self.write('/v2/income', {'account_id': account, 'amount': 10000, 'received_on': str(self.day), 'effect': 'add'})
        self.write('/v2/planning/steps/step-40/complete')
        data = self.get()
        plan = data['assistant']['plan']
        self.assertEqual((plan['cash'], plan['reserved'], plan['goal_saved'], plan['available']), (110000, 0, 4000, 16000))
        self.assertEqual(data['personal']['data']['accounts'][0]['balance'], plan['cash'])
        revisions = [data['revision'], data['personal']['revision'], data['assistant']['revision'], plan['revision'], data['assistant']['observations']['revision'], data['assistant']['lessons']['revision']]
        self.assertEqual(len(set(revisions)), 1)
        self.assertEqual(self.get('/v2/assistant/context'), data['assistant'])
        restarted = create_app(self.db, self.token, today=lambda: self.day, local_dir=self.folder)
        try:
            with TestClient(restarted) as client:
                self.assertEqual(client.get('/v2/frontend', headers=self.auth).json(), data)
        finally:
            restarted.state.store.engine.dispose()

    def test_preview_and_reads_do_not_change_any_exported_state(self):
        self.setup_plan()
        before = self.get('/v1/export')
        for path in ['/v2/frontend', '/v2/assistant/context']:
            self.get(path)
        response = self.client.post('/v2/planning/preview', headers=self.auth, json={'amount': 4000})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['remaining'], 6000)
        self.assertTrue(response.json()['eligible'])
        self.assertEqual(self.get('/v1/export'), before)

    def test_resume_retry_conflict_and_current_facts(self):
        self.setup_plan()
        self.write('/v2/planning/defer')
        self.assertEqual(self.get()['assistant']['plan']['recommendation_kind'], 'maintain')
        revision = self.get()['revision']
        first = self.write('/v2/planning/resume', {'revision': revision}, key='resume-retry-0001')
        retry = self.write('/v2/planning/resume', {'revision': revision}, key='resume-retry-0001')
        self.assertEqual(first, retry)
        self.assertEqual(first['recommendation_kind'], 'save')
        self.write('/v2/planning/resume', {'revision': revision}, key='resume-stale-0001', status=409)
        self.write('/v2/planning/resume', {'revision': revision+1}, key='resume-retry-0001', status=409)
        data = self.get()
        self.assertEqual(data['revision'], revision+1)

    def test_auth_and_cors_exact_origin(self):
        for path in ['/v2/frontend', '/v2/assistant/context']:
            self.assertEqual(self.client.get(path).status_code, 401)
        for origin, allowed in [(self.origin, True), ('https://untrusted.example', False), (self.origin+'.evil.example', False)]:
            preflight = self.client.options('/v2/planning/resume', headers={
                'Origin': origin, 'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'authorization,content-type,idempotency-key'})
            self.assertEqual(preflight.status_code, 200 if allowed else 400)
            self.assertEqual(preflight.headers.get('access-control-allow-origin'), origin if allowed else None)
        actual = self.client.get('/v2/frontend', headers={**self.auth, 'Origin': self.origin})
        self.assertEqual(actual.headers['access-control-allow-origin'], self.origin)

    def test_invalid_origins_rejected_before_storage_and_bootstrap_reads_once(self):
        invalid_db = self.folder / 'must-not-be-created.db'
        for origin in ['*', 'null', 'https://*.example.org', 'https://user:secret@example.org',
                       'https://example.org/path', 'https://example.org/', 'http://localhost:bad',
                       'https://example.org?query=1', 'https://example.org#fragment']:
            with self.assertRaises(ValueError):
                create_app(f'sqlite:///{invalid_db}', self.token, local_dir=self.folder, frontend_origins=[origin])
        self.assertFalse(invalid_db.exists())
        original_read = self.app.state.store.read
        reads = []
        def counted_read(owner):
            reads.append(owner)
            return original_read(owner)
        self.app.state.store.read = counted_read
        self.get()
        self.assertEqual(reads, ['local-demo'])

    def test_delete_clears_frontend_and_assistant_projections(self):
        self.setup_plan()
        self.assertEqual(self.client.delete('/v1/data', headers=self.auth).status_code, 200)
        data = self.get()
        self.assertEqual(data['revision'], 0)
        self.assertEqual(data['personal']['data']['accounts'], [])
        self.assertIsNone(data['assistant']['plan']['cash'])
        self.assertEqual(data['assistant']['observations']['transaction_count'], 0)
        self.assertEqual(data['assistant']['lessons']['completed_count'], 0)
