from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
import unittest
from unittest.mock import patch

from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
import httpx

from vela.fx import ECBRates
from vela.fx_routes import install_fx
from vela.personal import Account
from vela.store import Store, receipts
from sqlalchemy import select


class FXRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.store = Store(f'sqlite:///{Path(self.temp.name)/"synthetic-fx.db"}')
        self.day = date(2026, 10, 25)
        self.status, self.calls = 200, []
        def transport(request):
            self.calls.append(request)
            return httpx.Response(self.status, content=b'{"date":"2026-10-23","base":"HUF","quote":"EUR","rate":0.0025}')
        self.http = httpx.Client(transport=httpx.MockTransport(transport))
        self.rates = ECBRates(self.http, today=lambda: self.day)
        self.app = FastAPI()
        # Installer-level owner dependency seam, not a claim of JWT verification.
        def owner(authorization: Annotated[str | None, Header()] = None):
            owners = {'Bearer synthetic-A': 'A', 'Bearer synthetic-B': 'B'}
            if authorization not in owners:
                raise HTTPException(401, 'Synthetic credentials required.')
            return owners[authorization]
        install_fx(self.app, self.store, owner, lambda: self.day, rates=self.rates)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.http.close()
        self.store.engine.dispose()
        self.temp.cleanup()

    def seed(self, who, values):
        def apply(state):
            state.personal.accounts = [Account(id=f'account-{i}', name='Synthetic', currency=currency,
                                               balance=minor, confirmed_on=self.day if minor is not None else None)
                                       for i, (minor, currency) in enumerate(values)]
        return self.store.mutate(who, 'seed', 0, {'kind': 'fixture', 'values': values}, apply,
                                 lambda state: {'revision': state.revision})

    def get(self, who='A', suffix=''):
        return self.client.get('/v2/valuations/accounts'+suffix, headers={'Authorization': 'Bearer synthetic-'+who})

    def test_exact_contract_readonly_same_revision_and_originals(self):
        self.seed('A', [(1000, 'EUR'), (200, 'HUF'), (200, 'HUF')])
        before = self.store.read('A').model_dump_json()
        with self.store.engine.connect() as conn:
            before_receipts = conn.execute(select(receipts)).fetchall()
        response = self.get()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual((data['revision'], data['total_minor'], data['complete']), (1, 1001, True))
        self.assertEqual(data['rate_mode'], 'latest')
        self.assertEqual(data['balance_basis'], 'current_confirmed_balances')
        line = data['lines'][1]
        self.assertEqual(line['original'], {'amount_minor': 200, 'currency': 'HUF'})
        self.assertEqual(line['converted_minor_exact'], '0.5000')
        self.assertEqual(line['quote']['rate'], '0.0025')
        self.assertEqual(line['quote']['rate_date'], '2026-10-23')
        self.assertEqual(line['quote']['source'], 'ECB via Frankfurter v2')
        self.assertEqual(self.store.read('A').model_dump_json(), before)
        with self.store.engine.connect() as conn:
            self.assertEqual(conn.execute(select(receipts)).fetchall(), before_receipts)

    def test_owner_isolation_auth_and_no_query_owner_override(self):
        self.seed('A', [(1000, 'EUR')])
        self.seed('B', [(9000, 'EUR')])
        self.assertEqual(self.get('A', '?user_id=B').json()['total_minor'], 1000)
        self.assertEqual(self.get('B').json()['total_minor'], 9000)
        self.assertEqual(self.client.get('/v2/valuations/accounts').status_code, 401)
        self.assertEqual(self.get('foreign').status_code, 401)
        self.assertEqual(self.calls, [])

    def test_unknown_and_outage_are_incomplete_but_empty_is_known_empty(self):
        self.assertEqual(self.get().json()['total_minor'], 0)
        self.seed('A', [(1000, 'EUR'), (None, 'HUF')])
        unknown = self.get().json()
        self.assertFalse(unknown['complete'])
        self.assertIsNone(unknown['total_minor'])
        self.assertEqual(unknown['lines'][1]['unavailable'], 'unknown_amount')
        self.seed('B', [(200, 'HUF')])
        self.status = 503
        missing = self.get('B').json()
        self.assertIsNone(missing['total_minor'])
        self.assertEqual(missing['lines'][0]['unavailable'], 'missing_rate')

    def test_historical_is_labelled_current_balance_and_future_invalid(self):
        self.seed('A', [(40200, 'HUF')])
        data = self.get(suffix='?on=2026-10-24').json()
        self.assertEqual(data['rate_mode'], 'historical_reference')
        self.assertEqual(data['balance_basis'], 'current_confirmed_balances')
        self.assertEqual(data['requested_on'], '2026-10-24')
        self.assertEqual(data['total_minor'], 101)
        self.assertEqual(self.calls[0].url.params['date'], '2026-10-24')
        self.assertEqual(self.get(suffix='?on=2026-10-26').status_code, 422)
        self.assertEqual(self.get(suffix='?on=not-a-date').status_code, 422)

    def test_output_overflow_validation_not_unsafe_json_number(self):
        self.seed('A', [(9_007_199_254_740_991, 'EUR'), (1, 'EUR')])
        response = self.get()
        self.assertEqual(response.status_code, 422)
        self.assertIn('safe integer', response.json()['detail'])

    def test_default_provider_client_is_closed_after_cache_miss(self):
        from vela import fx_routes
        real = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(503)))
        with patch.object(fx_routes.httpx, 'Client', return_value=real):
            response = fx_routes._ClosedAfterRequestClient().get('https://api.frankfurter.dev/v2/providers/ecb/rate/huf/eur')
        self.assertEqual(response.status_code, 503)
        self.assertTrue(real.is_closed)

    def test_actual_factory_registers_verified_owner_and_injected_rates(self):
        from vela.main import create_app
        folder = Path(self.temp.name) / 'factory'
        app = create_app(f'sqlite:///{Path(self.temp.name)/"factory-synthetic.db"}',
                         'synthetic-fx-factory-token-2026', local_dir=folder,
                         today=lambda: self.day, fx_rates=self.rates)
        try:
            with TestClient(app) as client:
                self.assertEqual(client.get('/v2/valuations/accounts').status_code, 401)
                response = client.get('/v2/valuations/accounts', headers={
                    'Authorization': 'Bearer synthetic-fx-factory-token-2026'})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()['total_minor'], 0)
                self.assertEqual(self.calls, [])
        finally:
            app.state.store.engine.dispose()
