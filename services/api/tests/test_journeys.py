from datetime import date, timedelta
from tempfile import TemporaryDirectory
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest import mock
import asyncio
import json
import os
import random
import unittest
from fastapi.testclient import TestClient
from vela.domain import State, fixture, capacity, accept, complete, recommendation, Obligation, Snapshot, suggested_amount
from vela.main import create_app
from vela.ai import Quotas, MODELS
from vela import imports as imp
from vela import chat as chat_module

TODAY = date(2026, 10, 24)
TOKEN = 'test-only-token-at-least-24-characters'

GERMAN_CSV = """Kontoauszug Girokonto;;;;
IBAN;DE00 0000 0000 0000 0000 00;;;
;;;;
Buchungstag;Valuta;Auftraggeber/Empfänger;Verwendungszweck;Betrag;Saldo
01.10.2026;01.10.2026;ACME GmbH;Gehalt Oktober;2.500,00;3.100,00
02.10.2026;02.10.2026;Hausverwaltung Meier;Miete Oktober;-850,00;2.250,00
05.10.2026;05.10.2026;REWE Markt;Kartenzahlung;-63,47;2.186,53
01.09.2026;01.09.2026;ACME GmbH;Gehalt September;2.500,00;1.450,00
02.09.2026;02.09.2026;Hausverwaltung Meier;Miete September;-850,00;600,00
03.09.2026;03.09.2026;Netflix;Abo;-12,99;587,01
03.10.2026;03.10.2026;Netflix;Abo;-12,99;2.237,01
"""

ENGLISH_CSV = """Date,Description,Money Out,Money In,Balance
2026-10-20,TESCO STORES 123,45.10,,"1,954.90"
2026-10-18,Salary ACME LTD,,"2,000.00","2,000.00"
2026-10-21,Uber trip,12.00,,"1,942.90"
"""


def fake_response(text):
    return SimpleNamespace(text=text, model_version='fake')


class DomainTests(unittest.TestCase):
    def test_acceptance_fixture(self):
        state = State(snapshot=fixture(TODAY))
        self.assertEqual(capacity(state), 10000)
        with self.assertRaises(ValueError):
            accept(state, 15000, 'too-much', TODAY)
        accept(state, 4000, 'a', TODAY)
        self.assertEqual(state.snapshot.cash, 100000)
        self.assertEqual(state.snapshot.saved, 0)
        self.assertEqual(capacity(state), 6000)
        complete(state, 'a', TODAY)
        self.assertEqual(state.snapshot.cash, 100000)
        self.assertEqual(state.snapshot.saved, 4000)
        self.assertEqual(capacity(state), 6000)
        complete(state, 'a', TODAY)
        self.assertEqual(state.snapshot.saved, 4000)

    def test_new_cost_invalidates_action(self):
        state = State(snapshot=fixture(TODAY))
        accept(state, 4000, 'a', TODAY)
        state.snapshot.obligations.append(Obligation(id='new', label='Necessary cost', amount=8000, due=TODAY))
        self.assertEqual(capacity(state, 'a'), 2000)
        with self.assertRaises(ValueError):
            complete(state, 'a', TODAY)

    def test_unknown_and_stale(self):
        state = State(snapshot=fixture(TODAY))
        state.snapshot.debt_known = False
        rec = recommendation(state, TODAY)
        self.assertEqual((rec['kind'], rec['clarify_field']), ('clarify', 'debt_known'))
        state.snapshot.debt_known = True
        self.assertEqual(recommendation(state, TODAY+timedelta(days=8))['clarify_field'], 'refresh')

    def test_suggestion_policy(self):
        self.assertEqual(suggested_amount(10000, 50000), 2000)       # a fifth of €100
        self.assertEqual(suggested_amount(965000, 100000), 100000)   # capped by remaining goal
        self.assertEqual(suggested_amount(1200, 50000), 500)         # minimum €5
        self.assertEqual(suggested_amount(400, 50000), 0)            # too little free
        state = State(snapshot=fixture(TODAY))
        accept(state, 2000, 'a', TODAY)
        complete(state, 'a', TODAY)
        self.assertEqual(recommendation(state, TODAY)['kind'], 'save')  # keeps suggesting after a completed step

    def test_minor_units_strict_and_duplicate_obligations(self):
        payload = fixture(TODAY).model_dump()
        for invalid in [True, 10.5, '100', -1, 1_000_000_001]:
            with self.assertRaises(ValueError):
                Snapshot.model_validate({**payload, 'cash': invalid})
        with self.assertRaises(ValueError):
            Snapshot.model_validate({**payload, 'obligations': [payload['obligations'][0]]*2})

    def test_allocation_conservation_randomized(self):
        randomizer = random.Random(20261024)
        for _ in range(500):
            state = State(snapshot=fixture(TODAY))
            amount = randomizer.randint(1, 10000)
            accept(state, amount, 'a', TODAY)
            complete(state, 'a', TODAY)
            self.assertEqual(state.snapshot.cash, 100000)
            self.assertEqual(capacity(state) + state.snapshot.saved, 10000)


class ParserTests(unittest.TestCase):
    def test_amounts(self):
        cases = {('1.234,56', True): 123456, ('-63,47', True): -6347, ('1,234.56', False): 123456,
                 ('(12.30)', False): -1230, ('12.30-', False): -1230, ('€ 1 200,00', True): 120000,
                 ('−5.00', False): -500, ('', False): None, ('abc', False): None, ('01.10.2026', True): None}
        for (text, comma), expected in cases.items():
            self.assertEqual(imp.parse_amount(text, comma), expected, text)

    def test_german_csv_with_preamble(self):
        rows, warnings, closing = imp.tabular(imp.csv_rows(GERMAN_CSV), 'x.csv')
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[1]['amount'], -85000)
        self.assertEqual(rows[1]['date'], date(2026, 10, 2))
        self.assertIn('Hausverwaltung Meier', rows[1]['description'])
        self.assertEqual(closing, 218653)  # balance on the latest date (05.10.2026)

    def test_english_debit_credit_newest_balance(self):
        rows, _, closing = imp.tabular(imp.csv_rows(ENGLISH_CSV), 'x.csv')
        self.assertEqual([r['amount'] for r in rows], [-4510, 200000, -1200])
        self.assertEqual(closing, 194290)

    def test_categories_and_recurring(self):
        rows, _, _ = imp.tabular(imp.csv_rows(GERMAN_CSV), 'x.csv')
        for r in rows:
            r['category'] = imp.keyword_category(r['description'], r['amount'])
        cats = {r['description'].split(' · ')[0]: r['category'] for r in rows}
        self.assertEqual(cats['ACME GmbH'], 'income')
        self.assertEqual(cats['Hausverwaltung Meier'], 'housing')
        self.assertEqual(cats['REWE Markt'], 'groceries')
        recurring = imp.detect_recurring(rows, TODAY)
        rent = next(r for r in recurring if 'Hausverwaltung' in r.label)
        self.assertEqual((rent.amount, rent.kind, rent.next_due), (85000, 'rent', date(2026, 11, 2)))
        self.assertTrue(any('Netflix' in r.label for r in recurring))
        self.assertFalse(any('REWE' in r.label for r in recurring))

    def test_unsupported_file(self):
        with self.assertRaises(imp.ImportError_):
            imp.file_type('notes.docx', 'application/msword', b'\x00\x01\x02')

    def test_headerless_csv_and_pdf_lines(self):
        raw = "2026-10-01;Salary;2500,00\n2026-10-02;Rent;-850,00\n"
        rows, _, _ = imp.tabular(imp.csv_rows(raw), 'nohead.csv')
        self.assertEqual([r['amount'] for r in rows], [250000, -85000])
        pdf_rows = imp.parse_pdf_lines("01.10.2026 ACME Salary +2.500,00 EUR\n02.10.2026 Rent payment -850,00 EUR")
        self.assertEqual([r['amount'] for r in pdf_rows], [250000, -85000])


class APITests(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {'ENABLE_GEMINI': 'false'})
        self.env.start()
        self.tmp = TemporaryDirectory()
        path = Path(self.tmp.name)
        self.app = create_app(f'sqlite:///{path / "test.db"}', TOKEN, lambda: TODAY, path)
        self.client = TestClient(self.app)
        self.headers = {'Authorization': f'Bearer {TOKEN}'}
        self.counter = 0

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        self.tmp.cleanup()
        self.env.stop()

    def post(self, route, payload, key=None):
        self.counter += 1
        return self.client.post('/v1/'+route, json=payload,
                                headers={**self.headers, 'Idempotency-Key': key or f'command-{self.counter:06d}'})

    def load(self):
        response = self.post('demo', {'revision': 0})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def upload(self, name, content, mime='text/csv'):
        return self.client.post('/v1/imports', files={'file': (name, content, mime)}, headers=self.headers)

    def test_full_journey_and_retry(self):
        initial = self.load()
        self.assertEqual(initial['available'], 10000)
        self.assertEqual(initial['recommendation']['amount'], 2000)
        self.assertEqual(initial['breakdown'], {'cash': 100000, 'saved': 0, 'protected': 10000, 'bills': 80000, 'planned': 0})
        response = self.post('actions', {'revision': 1, 'amount': 4000}, 'same-request')
        self.assertEqual(response.status_code, 200, response.text)
        planned = response.json()
        repeated = self.post('actions', {'revision': 1, 'amount': 4000}, 'same-request')
        self.assertEqual(repeated.json(), planned)
        self.assertEqual(self.post('actions', {'revision': 1, 'amount': 5000}, 'same-request').status_code, 409)
        done = self.post(f'actions/{planned["actions"][0]["id"]}/complete', {'revision': 2}).json()
        self.assertEqual(done['snapshot']['saved'], 4000)
        self.assertEqual(done['snapshot']['cash'], 100000)
        self.assertEqual(done['available'], 6000)

    def test_auth_and_stale_revision(self):
        for method, route in [('get', '/v1/state'), ('get', '/v1/export'), ('delete', '/v1/data'),
                              ('get', '/v1/transactions'), ('get', '/v1/ai/status')]:
            self.assertEqual(getattr(self.client, method)(route).status_code, 401, route)
        self.assertEqual(self.client.post('/v1/imports', files={'file': ('a.csv', b'x', 'text/csv')}).status_code, 401)
        self.assertEqual(self.client.post('/v1/chat', json={'messages': [{'role': 'user', 'content': 'hi'}]}).status_code, 401)
        self.load()
        self.assertEqual(self.post('actions', {'revision': 0, 'amount': 4000}).status_code, 409)

    def test_confirm_clears_clarify(self):
        self.load()
        snap = self.client.get('/v1/state', headers=self.headers).json()['snapshot']
        snap.update(debt_known=False, obligations_complete=False, provenance='manual')
        state = self.client.put('/v1/snapshot', json={'revision': 1, 'snapshot': snap},
                                headers={**self.headers, 'Idempotency-Key': 'put-snapshot-1'}).json()
        self.assertEqual(state['recommendation']['clarify_field'], 'debt_known')
        state = self.post('confirm', {'revision': 2, 'field': 'debt_known'}).json()
        self.assertEqual(state['recommendation']['clarify_field'], 'obligations_complete')
        state = self.post('confirm', {'revision': 3, 'field': 'obligations_complete'}).json()
        self.assertEqual(state['recommendation']['kind'], 'save')

    def test_bill_paid_and_removed(self):
        self.load()
        paid = self.post('obligations/rent/done', {'revision': 1, 'paid': True}).json()
        self.assertEqual(paid['snapshot']['cash'], 40000)
        self.assertNotIn('rent', [o['id'] for o in paid['snapshot']['obligations']])
        self.assertEqual(paid['available'], 10000)  # paying a bill doesn't change what's free
        removed = self.post('obligations/debt/done', {'revision': 2, 'paid': False}).json()
        self.assertEqual(removed['snapshot']['cash'], 40000)
        self.assertEqual(removed['available'], 15000)
        self.assertEqual(self.post('obligations/missing/done', {'revision': 3, 'paid': True}).status_code, 422)

    def test_add_bill(self):
        self.load()
        r = self.post('obligations', {'revision': 1, 'obligation': {'id': 'gym', 'label': 'Gym', 'amount': 3000,
                                                                    'due': (TODAY+timedelta(days=3)).isoformat(), 'kind': 'other'}})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['available'], 7000)
        late = self.post('obligations', {'revision': 2, 'obligation': {'id': 'late', 'label': 'Late', 'amount': 3000,
                                                                       'due': (TODAY+timedelta(days=90)).isoformat(), 'kind': 'other'}})
        self.assertEqual(late.status_code, 422)

    def test_income_already_in_snapshot_not_added(self):
        self.load()
        result = self.post('income', {'revision': 1, 'amount': 60000, 'event_id': 'income-001',
                                     'received_on': TODAY.isoformat(), 'already_in_balance': True})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['snapshot']['cash'], 100000)
        duplicate = self.post('income', {'revision': 2, 'amount': 60000, 'event_id': 'income-001',
                                         'received_on': TODAY.isoformat(), 'already_in_balance': True})
        self.assertEqual(duplicate.status_code, 422)

    def test_preview_is_read_only(self):
        self.load()
        preview = self.client.post('/v1/preview', json={'amount': 15000}, headers=self.headers).json()
        self.assertFalse(preview['eligible'])
        self.assertTrue(self.client.post('/v1/preview', json={'amount': 3000}, headers=self.headers).json()['eligible'])
        self.assertEqual(self.client.get('/v1/state', headers=self.headers).json()['revision'], 1)

    def test_concurrent_accept_one_wins(self):
        self.load()
        def attempt(i):
            return self.client.post('/v1/actions', json={'revision': 1, 'amount': 4000},
                                    headers={**self.headers, 'Idempotency-Key': f'parallel-{i}'}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(attempt, [1, 2]))
        self.assertEqual(sorted(codes), [200, 409])

    def test_shortfall_disables_completion(self):
        self.load()
        planned = self.post('actions', {'revision': 1, 'amount': 4000}).json()
        response = self.post('obligations', {'revision': 2, 'obligation': {'id': 'extra', 'label': 'Repair', 'amount': 8000,
                                                                         'due': TODAY.isoformat(), 'kind': 'other'}})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json()['actions'][0]['can_complete'])
        self.assertEqual(self.post(f'actions/{planned["actions"][0]["id"]}/complete', {'revision': 3}).status_code, 422)

    def test_csv_import_creates_snapshot_and_bills(self):
        preview = self.upload('giro.csv', GERMAN_CSV.encode('cp1252'))
        self.assertEqual(preview.status_code, 200, preview.text)
        p = preview.json()
        self.assertEqual((p['parser'], len(p['transactions']), p['closing_balance']), ('local', 7, 218653))
        self.assertEqual(p['income'], 500000)
        self.assertIn('Categories were guessed from keywords.', p['warnings'])
        rent = next(r for r in p['recurring'] if r['kind'] == 'rent')
        self.assertEqual(self.client.get(f'/v1/imports/{p["id"]}', headers=self.headers).json()['id'], p['id'])
        state = self.post(f'imports/{p["id"]}/apply', {'revision': 0, 'cash': 218653, 'obligation_ids': [rent['id']]})
        self.assertEqual(state.status_code, 200, state.text)
        s = state.json()
        self.assertEqual(s['snapshot']['cash'], 218653)
        self.assertEqual(s['snapshot']['provenance'], 'import')
        self.assertEqual([o['amount'] for o in s['snapshot']['obligations']], [85000])
        self.assertEqual(s['summary']['transaction_count'], 7)
        self.assertEqual(s['recommendation']['clarify_field'], 'debt_known')
        txns = self.client.get('/v1/transactions', headers=self.headers).json()
        self.assertEqual(txns['total'], 7)
        self.assertEqual(txns['transactions'][0]['date'], '2026-10-05')
        # Re-importing the same file adds no duplicate transactions.
        again = self.upload('giro.csv', GERMAN_CSV.encode('cp1252')).json()
        s2 = self.post(f'imports/{again["id"]}/apply', {'revision': 1}).json()
        self.assertEqual(s2['summary']['transaction_count'], 7)
        self.assertEqual(s2['snapshot']['cash'], 218653)

    def test_import_into_existing_snapshot_updates_balance(self):
        self.load()
        p = self.upload('bank.csv', ENGLISH_CSV.encode()).json()
        s = self.post(f'imports/{p["id"]}/apply', {'revision': 1, 'cash': 194290}).json()
        self.assertEqual(s['snapshot']['cash'], 194290)
        self.assertEqual(s['snapshot']['as_of'], TODAY.isoformat())
        self.assertEqual(len(s['snapshot']['obligations']), 3)

    def test_import_errors(self):
        self.assertEqual(self.upload('x.docx', b'\x00\x01\x02', 'application/msword').status_code, 422)
        self.assertEqual(self.upload('x.csv', b'', 'text/csv').status_code, 422)
        bad = self.upload('x.csv', b'foo,bar\n1,2\n', 'text/csv')
        self.assertEqual(bad.status_code, 422)
        pdf = self.upload('s.pdf', b'%PDF-1.4 test', 'application/pdf')
        self.assertEqual(pdf.status_code, 422)
        self.assertIn('AI service is turned off', pdf.json()['detail'])
        self.assertEqual(self.post('imports/imp-missing/apply', {'revision': 0}).status_code, 404)
        first = self.upload('bank.csv', ENGLISH_CSV.encode()).json()
        self.assertEqual(self.post(f'imports/{first["id"]}/apply', {'revision': 0}).status_code, 422)  # needs a balance
        import base64
        b64 = base64.b64encode(ENGLISH_CSV.encode()).decode()
        r64 = self.client.post('/v1/imports/base64', json={'filename': 'bank.csv', 'content_type': 'text/csv', 'data_base64': b64}, headers=self.headers)
        self.assertEqual(r64.status_code, 200, r64.text)
        self.assertEqual(len(r64.json()['transactions']), 3)

    def test_pdf_import_with_mocked_gemini(self):
        statement = {'currency': 'EUR', 'opening_balance': 100.0, 'closing_balance': 50.0, 'transactions': [
            {'date': '2026-10-10', 'description': 'Spotify', 'amount': -10.99, 'category': 'subscriptions'},
            {'date': '2026-10-12', 'description': 'Lidl', 'amount': -39.01, 'category': 'groceries'}]}
        async def fake_generate(quotas, route, contents, config, tokens, timeout_ms=0):
            self.assertEqual(route, 'document')
            return fake_response(json.dumps(statement)), MODELS[1]
        with mock.patch.object(imp, 'generate', fake_generate):
            r = self.upload('statement.pdf', b'%PDF-1.4 fake', 'application/pdf')
        self.assertEqual(r.status_code, 200, r.text)
        p = r.json()
        self.assertEqual((p['parser'], p['model'], p['closing_balance'], p['spending']), ('gemini', MODELS[1], 5000, 5000))
        self.assertEqual(p['warnings'], [])
        statement['closing_balance'] = 80.0
        with mock.patch.object(imp, 'generate', fake_generate):
            warn = self.upload('statement.pdf', b'%PDF-1.4 fake', 'application/pdf').json()
        self.assertTrue(any('differs from the closing balance' in w for w in warn['warnings']))

    def test_chat_local_fallback_and_mocked_gemini(self):
        self.load()
        body = {'messages': [{'role': 'user', 'content': 'How much can I save?'}]}
        local = self.client.post('/v1/chat', json=body, headers=self.headers)
        self.assertEqual(local.status_code, 200, local.text)
        self.assertEqual(local.json()['source'], 'local')
        self.assertIn('€100.00', local.json()['reply'])
        captured = {}
        async def fake_generate(quotas, route, contents, config, tokens, timeout_ms=0):
            captured.update(route=route, contents=contents, system=config['system_instruction'])
            return fake_response('You have **€100.00** free.'), MODELS[0]
        with mock.patch.object(chat_module, 'generate', fake_generate):
            body['messages'] += [{'role': 'assistant', 'content': 'Hi'}, {'role': 'user', 'content': 'And rent?'}]
            reply = self.client.post('/v1/chat', json=body, headers=self.headers).json()
        self.assertEqual((reply['source'], reply['model']), ('gemini', MODELS[0]))
        self.assertEqual(captured['route'], 'chat')
        self.assertEqual([c['role'] for c in captured['contents']], ['user', 'model', 'user'])
        self.assertIn('"available": "€100.00"', captured['system'])
        self.assertEqual(self.client.post('/v1/chat', json={'messages': [{'role': 'assistant', 'content': 'x'}]},
                                          headers=self.headers).status_code, 422)

    def test_ai_status(self):
        status = self.client.get('/v1/ai/status', headers=self.headers).json()
        self.assertFalse(status['enabled'])
        self.assertEqual(status['routes'], {'chat': MODELS[0], 'document': MODELS[1], 'categorize': MODELS[1]})
        self.assertEqual([m['model'] for m in status['models']], list(MODELS))

    def test_delete_clears_everything(self):
        p = self.upload('bank.csv', ENGLISH_CSV.encode()).json()
        self.post(f'imports/{p["id"]}/apply', {'revision': 0, 'cash': 194290})
        self.assertEqual(self.client.delete('/v1/data', headers=self.headers).status_code, 200)
        self.assertIsNone(self.client.get('/v1/state', headers=self.headers).json()['snapshot'])
        self.assertEqual(self.client.get('/v1/transactions', headers=self.headers).json()['total'], 0)
        self.assertEqual(self.client.get(f'/v1/imports/{p["id"]}', headers=self.headers).status_code, 404)
        self.assertEqual(self.post('demo', {'revision': 0}, 'command-000001').status_code, 200)


class QuotaTests(unittest.TestCase):
    def test_limits_fallback_and_restart(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)/'quota.db'
            q = Quotas(path)
            for _ in range(12):
                self.assertEqual(q.reserve(MODELS[0], now=1000), MODELS[0])
            self.assertEqual(Quotas(path).reserve(MODELS[0], now=1000), MODELS[1])
            for _ in range(11):
                self.assertEqual(q.reserve(MODELS[0], now=1000), MODELS[1])
            self.assertIsNone(q.reserve(MODELS[0], now=1000))
            self.assertEqual(q.reserve(MODELS[0], now=1061), MODELS[0])
            self.assertEqual(q.usage(now=1061)[0]['requests_today'], 13)

    def test_token_budget(self):
        with TemporaryDirectory() as tmp:
            q = Quotas(Path(tmp)/'quota.db')
            self.assertEqual(q.reserve(MODELS[0], tokens=225000, now=1000), MODELS[0])
            self.assertEqual(q.reserve(MODELS[0], now=1000), MODELS[1])
            self.assertIsNone(q.reserve(MODELS[0], tokens=250001, now=1000))

    def test_generate_falls_back_to_other_model(self):
        from vela import ai
        calls = []

        class RateLimited(Exception):
            code = 429

        class FakeModels:
            async def generate_content(self, model, contents, config):
                calls.append(model)
                if model == MODELS[0]:
                    raise RateLimited()
                return fake_response('ok')

        class FakeAio:
            models = FakeModels()
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False

        class FakeClient:
            def __init__(self, **kw): self.aio = FakeAio()

        with TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {'ENABLE_GEMINI': 'true', 'GEMINI_API_KEY': 'x'}), \
                mock.patch('google.genai.Client', FakeClient):
            q = Quotas(Path(tmp)/'quota.db')
            response, model = asyncio.run(ai.generate(q, 'chat', 'hi', {}, 100))
            self.assertEqual((response.text, model, calls), ('ok', MODELS[1], [MODELS[0], MODELS[1]]))
            self.assertTrue(q.usage()[0]['cooling_down'])
