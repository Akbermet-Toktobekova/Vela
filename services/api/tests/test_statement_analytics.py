import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from vela.main import create_app
from vela.domain import Transaction
from vela.tools import calculate_cash_flow


class StatementAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.app = create_app(f"sqlite:///{self.path/'test.db'}", 'analytics-test-token-at-least-24-characters',
                              today=lambda: date(2026, 10, 29), local_dir=self.path)
        self.client = TestClient(self.app)
        self.headers = {'Authorization': 'Bearer analytics-test-token-at-least-24-characters'}
        self.fixtures = Path(__file__).resolve().parents[3] / 'docs/testing/pattern-statements'

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        self.temp.cleanup()

    def get(self, path):
        response = self.client.get(path, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def post(self, path, body, key):
        return self.client.post(path, json=body, headers={**self.headers, 'Idempotency-Key': key})

    def upload(self, month):
        file = self.fixtures / f'SYNTHETIC-2026-{month}-EUR.csv'
        response = self.client.post('/v1/imports', headers=self.headers,
                                    files={'file': (file.name, file.read_bytes(), 'text/csv')})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def apply(self, preview, key):
        return self.post(f"/v2/imports/{preview['id']}/apply", {'revision': self.get('/v1/state')['revision']}, key)

    def test_new_import_without_profile_has_no_hidden_financial_defaults(self):
        before = self.get('/v1/export')
        preview = self.upload('07')
        applied = self.apply(preview, 'analytics-empty-01')
        self.assertEqual(applied.status_code, 200, applied.text)
        after = self.get('/v1/export')
        for field in ('personal', 'snapshot', 'actions', 'debts', 'income_ids', 'deferred'):
            self.assertEqual(after[field], before[field], field)
        self.assertEqual(len(after['transactions']), 16)
        self.assertEqual(self.post(f"/v2/imports/{preview['id']}/apply",
                                  {'revision': 1, 'cash': 999}, 'analytics-invalid-01').status_code, 422)
        self.assertEqual(self.client.get('/v2/observations').status_code, 401)

    def test_fixture_refund_and_cumulative_evidence_and_repeat_preserve_money(self):
        self.assertEqual(self.post('/v1/demo', {'revision': 0}, 'analytics-demo-01').status_code, 200)
        account = self.post('/v2/accounts', {'revision': 1, 'name': 'Known account', 'currency': 'EUR',
                            'balance': 123400, 'confirmed_on': '2026-10-29'}, 'analytics-account-01')
        self.assertEqual(account.status_code, 200, account.text)
        accepted = self.post('/v1/actions', {'revision': 2, 'amount': 2000}, 'analytics-plan-01')
        action_id = accepted.json()['actions'][0]['id']
        self.assertEqual(self.post(f'/v1/actions/{action_id}/complete', {'revision': 3}, 'analytics-complete-01').status_code, 200)
        self.assertEqual(self.post('/v1/actions', {'revision': 4, 'amount': 1000}, 'analytics-plan-02').status_code, 200)
        before = self.get('/v1/export')
        for month, count in [('07', 16), ('08', 36), ('09', 56)]:
            preview = self.upload(month)
            if month == '08':
                self.assertEqual(preview['income'], 150000)
                self.assertEqual(preview['refunds'], 2000)
                self.assertEqual(preview['net_spending'], 84298)
            result = self.apply(preview, 'analytics-import-'+month)
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.json()['summary']['transaction_count'], count)
            if month == '08':
                flow = calculate_cash_flow(self.app.state.store.read('local-demo'))
                self.assertEqual(flow['income_cents'], 150000)
                self.assertEqual(flow['refund_cents'], 2000)
                self.assertEqual(flow['net_cash_flow_cents'], 65702)
        after = self.get('/v1/export')
        for field in ('personal', 'snapshot', 'actions', 'debts', 'income_ids', 'deferred'):
            self.assertEqual(after[field], before[field], field)
        observations = self.get('/v2/observations')
        items = observations['observations']
        price = next(o for o in items if o['kind'] == 'price_change' and 'Stream Cedar' in o['label'])
        self.assertEqual(price['amounts'], [999, 999, 1299])
        self.assertEqual(price['difference'], 300)
        self.assertEqual(len(price['evidence_ids']), 3)
        gym = next(o for o in items if o['kind'] == 'recurring_payment' and 'Fit Cedar' in o['label'])
        self.assertEqual(gym['amounts'], [2500, 2500, 2500])
        self.assertTrue(all(o['status'] == 'suggested' and o['method_version'] and o['evidence_ids'] for o in items))
        ref = next(o for o in items if o['kind'] == 'refund_link')
        self.assertEqual(len(ref['evidence_ids']), 2)
        first = self.get('/v1/transactions?limit=50&offset=0')
        second = self.get('/v1/transactions?limit=50&offset=50')
        self.assertEqual(len(first['transactions']), 50)
        self.assertEqual(len(second['transactions']), 6)
        self.assertEqual(len({t['id'] for t in first['transactions']+second['transactions']}), 56)
        retry_preview = self.upload('09')
        command = {'revision': after['revision']}
        url = f"/v2/imports/{retry_preview['id']}/apply"
        applied = self.post(url, command, 'analytics-repeat-01')
        retry = self.post(url, command, 'analytics-repeat-01')
        self.assertEqual(applied.json(), retry.json())
        self.assertEqual(applied.json()['summary']['transaction_count'], 56)
        self.assertEqual(self.post(url, command, 'analytics-stale-01').status_code, 409)

    def test_future_statement_credit_never_funds_a_plan(self):
        self.assertEqual(self.post('/v1/demo', {'revision': 0}, 'analytics-demo-01').status_code, 200)
        before = self.get('/v1/state')
        response = self.client.post('/v1/imports', headers=self.headers,
                                    files={'file': ('future.csv', b'Date,Description,Amount\n2026-11-05,Salary,500.00\n', 'text/csv')})
        self.assertEqual(response.status_code, 200, response.text)
        result = self.apply(response.json(), 'analytics-future-01')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['available'], before['available'])

    def test_non_eur_cannot_be_silently_saved_as_eur(self):
        response = self.client.post('/v1/imports', headers=self.headers,
                                    files={'file': ('huf.csv', b'Date,Description,Amount,Currency\n2026-10-28,Test salary,100.00,HUF\n', 'text/csv')})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['currency'], 'HUF')
        self.assertEqual(self.apply(response.json(), 'analytics-huf-01').status_code, 422)
        self.assertEqual(self.get('/v1/export')['transactions'], [])

    def test_reimport_upgrades_old_refund_category_without_changing_money(self):
        preview = self.upload('08')
        result = self.apply(preview, 'analytics-refund-01')
        self.assertEqual(result.status_code, 200, result.text)
        store = self.app.state.store
        def old_category(s):
            next(t for t in s.transactions if t.category == 'refunds').category = 'income'
        current = store.read('local-demo')
        store.mutate('local-demo', 'simulate-old-refund', current.revision, {'kind': 'old-category-fixture'}, old_category, lambda s: {})
        before = self.get('/v1/export')
        self.assertEqual(self.apply(preview, 'analytics-refund-02').status_code, 200)
        after = self.get('/v1/export')
        self.assertEqual(after['snapshot'], before['snapshot'])
        self.assertEqual(len(after['transactions']), len(before['transactions']))
        self.assertEqual(self.get('/v1/state')['summary']['income'], 150000)

    def test_history_limit_rejects_import_without_dropping_old_entries(self):
        store = self.app.state.store
        def fill(s):
            s.transactions = [Transaction(id=f'old-{i}', date=date(2026, 1, 1),
                                           description=f'Old booked entry {i}', amount=-100) for i in range(3000)]
        store.mutate('local-demo', 'seed-full-history', 0, {'kind': 'history-fixture'}, fill, lambda s: {})
        before = self.get('/v1/export')
        result = self.apply(self.upload('07'), 'analytics-overflow-01')
        self.assertEqual(result.status_code, 422, result.text)
        self.assertEqual(self.get('/v1/export'), before)
