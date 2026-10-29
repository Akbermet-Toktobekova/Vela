import asyncio
from contextlib import redirect_stdout
from io import StringIO
import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

import httpx
from fastapi import Request
from fastapi.testclient import TestClient

from vela.main import create_app
from vela.logging_setup import correlation_id, RequestJSONFormatter, RequestPrivacyFilter


class CorrelationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        folder = Path(self.temp.name)
        self.output = StringIO()
        self.root_handlers = list(logging.getLogger().handlers)
        self.token = 'correlation-only-synthetic-test-token'
        self.origin = 'https://frontend.synthetic.example'
        with redirect_stdout(self.output):
            self.app = create_app(f'sqlite:///{folder / "correlation.db"}', self.token, local_dir=folder,
                                  frontend_origins=[self.origin])
        self.client = TestClient(self.app)
        self.auth = {'Authorization': 'Bearer '+self.token}

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        self.temp.cleanup()
        self.assertEqual(logging.getLogger().handlers, self.root_handlers)
        self.assertIsNone(correlation_id.get())

    def records(self):
        return [json.loads(line) for line in self.output.getvalue().splitlines() if line]

    def test_missing_provided_and_invalid_correlation_ids(self):
        missing = self.client.get('/health')
        UUID(missing.headers['x-correlation-id'])
        supplied = 'aabbccddeeff00112233445566778899'
        response = self.client.get('/health', headers={'X-Correlation-ID': supplied})
        self.assertEqual(response.headers['x-correlation-id'], supplied)
        canonical = '918d797c-977c-4b9a-b53f-1839883fbd88'
        self.assertEqual(self.client.get('/health', headers={'X-Correlation-ID': canonical}).headers['x-correlation-id'], canonical)
        for invalid in ['email@example.org', '123', 'x'*1000, 'name salary 100000', 'aabbccddeeff0011\r\nInjected:secret']:
            response = self.client.get('/health', headers={'X-Correlation-ID': invalid})
            generated = response.headers['x-correlation-id']
            UUID(generated)
            self.assertNotEqual(generated, invalid)
        duplicate = self.client.get('/health', headers=[('X-Correlation-ID', supplied), ('X-Correlation-ID', canonical)])
        UUID(duplicate.headers['x-correlation-id'])

    def test_handled_failures_keep_id_and_logs_exclude_sensitive_data(self):
        cid = 'aabbccddeeff00112233445566778899'
        headers = {**self.auth, 'X-Correlation-ID': cid, 'Idempotency-Key': 'sensitive-retry-label'}
        requests = [
            self.client.get('/v2/frontend?email=alice@example.org', headers={'X-Correlation-ID': cid}),
            self.client.post('/v2/income?memo=private-rent', headers=headers,
                             json={'revision': 0, 'account_id': 'private-account-name', 'amount': 987654, 'received_on': 'bad', 'effect': 'add'}),
            self.client.put('/v2/profile', headers=headers, json={'revision': 99, 'focus': 'unsure', 'income_type': 'unknown'}),
            self.client.get('/v1/lessons/private-person-transaction', headers=headers),
        ]
        self.assertEqual([r.status_code for r in requests], [401, 422, 409, 404])
        for response in requests:
            self.assertEqual(response.headers['x-correlation-id'], cid)
        records = self.records()
        self.assertEqual([r['status'] for r in records], [401, 422, 409, 404])
        self.assertEqual(records[-1]['route'], '/v1/lessons/{lesson_id}')
        text = self.output.getvalue()
        for secret in [self.token, 'alice', 'private-rent', 'private-account-name', '987654', 'sensitive-retry-label', 'private-person-transaction', 'information changed']:
            self.assertNotIn(secret, text)
        for record in records:
            self.assertEqual(set(record), {'event','correlation_id','method','route','status','duration_ms'})

    def test_concurrent_request_contexts_are_isolated_and_reset(self):
        seen = []
        @self.app.get('/correlation-test/{opaque}')
        async def overlap(opaque: str, request: Request):
            before = correlation_id.get()
            await asyncio.sleep(.02)
            seen.append((before, correlation_id.get(), request.state.correlation_id))
            return {'correlation_id': correlation_id.get()}

        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url='http://test') as client:
                expected = [f'{n:032x}' for n in range(1, 13)]
                responses = await asyncio.gather(*[client.get('/correlation-test/private-raw-path', headers={'X-Correlation-ID': cid}) for cid in expected])
                self.assertEqual([r.headers['x-correlation-id'] for r in responses], expected)
                self.assertEqual([r.json()['correlation_id'] for r in responses], expected)
            self.assertIsNone(correlation_id.get())
        asyncio.run(run())
        self.assertEqual(len(seen), 12)
        self.assertTrue(all(a == b == c for a,b,c in seen))
        self.assertEqual(len({r['correlation_id'] for r in self.records()}), 12)
        self.assertNotIn('private-raw-path', self.output.getvalue())

    def test_formatter_and_filter_discard_arbitrary_payload_and_exceptions(self):
        record = logging.LogRecord('test', logging.ERROR, '', 1, 'alice@example.org balance987654', (), None)
        record.event = 'http_request'
        record.correlation_id = 'person@example.org'
        record.method, record.route = 'GET', '/v1/lessons/{lesson_id}'
        record.status, record.duration_ms = 422, 2
        record.payload, record.exc_text = {'transaction': 'secret salary'}, 'private exception987654'
        self.assertTrue(RequestPrivacyFilter().filter(record))
        encoded = RequestJSONFormatter().format(record)
        self.assertNotIn('alice', encoded)
        self.assertNotIn('salary', encoded)
        self.assertNotIn('987654', encoded)
        UUID(json.loads(encoded)['correlation_id'])
        record.event = 'arbitrary_event'
        self.assertFalse(RequestPrivacyFilter().filter(record))

    def test_cors_exposes_id_and_unhandled_exception_logs_no_private_text(self):
        @self.app.get('/correlation-failure')
        async def failure():
            raise RuntimeError('private financial exception: salary987654 alice@example.org')
        response = self.client.options('/v2/frontend', headers={
            'Origin': self.origin, 'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization,x-correlation-id'})
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/health', headers={'Origin': self.origin})
        self.assertIn('X-Correlation-ID', response.headers['access-control-expose-headers'])
        supplied = 'ab12'*8
        with TestClient(self.app, raise_server_exceptions=False) as client:
            failure = client.get('/correlation-failure', headers={'X-Correlation-ID': supplied})
            self.assertEqual(failure.status_code, 500)
            self.assertEqual(failure.headers['x-correlation-id'], supplied)
            self.assertEqual(failure.json(), {'detail': 'The server could not complete this request.'})
            allowed = client.get('/correlation-failure', headers={'Origin': self.origin, 'X-Correlation-ID': supplied})
            self.assertEqual(allowed.status_code, 500)
            self.assertEqual(allowed.headers['access-control-allow-origin'], self.origin)
            self.assertEqual(allowed.headers['access-control-expose-headers'], 'X-Correlation-ID')
            self.assertEqual(allowed.headers['x-correlation-id'], supplied)
            self.assertEqual(allowed.headers['vary'], 'Origin')
            for disallowed in ['https://untrusted.example', self.origin+'.evil.example', 'http://localhost:8081', 'null']:
                blocked = client.get('/correlation-failure', headers={'Origin': disallowed, 'X-Correlation-ID': supplied})
                self.assertEqual(blocked.status_code, 500)
                self.assertNotIn('access-control-allow-origin', blocked.headers)
                self.assertNotIn('access-control-expose-headers', blocked.headers)
                self.assertEqual(blocked.headers['x-correlation-id'], supplied)
            generated = client.get('/correlation-failure')
            self.assertEqual(generated.status_code, 500)
            UUID(generated.headers['x-correlation-id'])
        self.assertIsNone(correlation_id.get())
        self.assertEqual(self.records()[-1]['status'], 500)
        self.assertEqual(self.records()[-1]['correlation_id'], generated.headers['x-correlation-id'])
        self.assertNotIn('salary', self.output.getvalue())
        self.assertNotIn('alice', self.output.getvalue())
