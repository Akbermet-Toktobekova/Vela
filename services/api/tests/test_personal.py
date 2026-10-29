import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from vela.main import create_app
from vela.domain import State


class PersonalPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.url = f"sqlite:///{self.path / 'test.db'}"
        self.token = 'personal-test-token-at-least-24-characters'
        self.app = create_app(self.url, self.token, today=lambda: date(2026, 10, 29), local_dir=self.path)
        self.client = TestClient(self.app)
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        self.temp.cleanup()

    def command(self, path, body, key, method='POST'):
        return self.client.request(method, path, json=body, headers={**self.headers, 'Idempotency-Key': key})

    def test_retry_conflict_restart_and_legacy_preservation(self):
        before = self.app.state.store.read('local-demo')
        response = self.command('/v2/accounts', dict(revision=0, name='Main', currency='HUF', balance=100000, confirmed_on='2026-10-29'), 'account-0001')
        self.assertEqual(response.status_code, 200, response.text)
        account_id = response.json()['data']['accounts'][0]['id']
        income = dict(revision=1, account_id=account_id, amount=20000, received_on='2026-10-29', effect='add')
        first = self.command('/v2/income', income, 'income-00001')
        retry = self.command('/v2/income', income, 'income-00001')
        self.assertEqual(first.json(), retry.json())
        self.assertEqual(first.json()['data']['accounts'][0]['balance'], 120000)
        self.assertEqual(len(first.json()['data']['incomes']), 1)
        self.assertEqual(self.command('/v2/income', income, 'income-00002').status_code, 409)
        included = self.command('/v2/income', {**income, 'revision': 2, 'effect': 'included'}, 'income-00003')
        self.assertEqual(included.json()['data']['accounts'][0]['balance'], 120000)
        self.assertEqual(self.app.state.store.read('local-demo').snapshot, before.snapshot)
        self.assertEqual(self.client.get('/v1/state', headers=self.headers).status_code, 200)
        other = self.app.state.store.read('different-owner')
        self.assertEqual(other.personal.accounts, [])
        restarted = create_app(self.url, self.token, today=lambda: date(2026, 10, 29), local_dir=self.path)
        try:
            with TestClient(restarted) as c:
                saved = c.get('/v2/personal', headers=self.headers).json()
                self.assertEqual(saved['data']['accounts'][0]['balance'], 120000)
                self.assertEqual(len(saved['data']['incomes']), 2)
        finally:
            restarted.state.store.engine.dispose()

    def test_unknown_balance_validation_profile_and_delete(self):
        self.assertEqual(self.client.get('/v2/personal').status_code, 401)
        self.assertEqual(State.model_validate({}).personal.accounts, [])
        a = self.command('/v2/accounts', dict(revision=0, name='Unknown', currency='EUR', confirmed_on='2026-10-29'), 'account-0001').json()
        account_id = a['data']['accounts'][0]['id']
        body = dict(revision=1, account_id=account_id, amount=100, received_on='2026-10-29', effect='add')
        self.assertEqual(self.command('/v2/income', body, 'income-00001').status_code, 422)
        self.assertEqual(self.command('/v2/income', {**body, 'effect': 'replace', 'current_balance': 5000}, 'income-00002').status_code, 200)
        profile = self.command('/v2/profile', dict(revision=2, focus='spending', income_type='irregular'), 'profile-0001', 'PUT')
        self.assertTrue(profile.json()['data']['onboarded'])
        invalid = self.command('/v2/accounts', dict(revision=3, name='Bad', currency='USD', balance=1.2, confirmed_on='2026-10-29'), 'account-0002')
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(self.client.delete('/v1/data', headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get('/v2/personal', headers=self.headers).json()['data']['accounts'], [])
