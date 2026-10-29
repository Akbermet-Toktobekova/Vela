"""Generated JWTs, mocked trusted JWKS and disposable two-owner SQLite only."""
from datetime import date
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient
import httpx
import jwt

from vela.auth import SupabaseJWTConfig, SupabaseJWTVerifier
from vela.main import create_app
from vela.store import Conflict


class IsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = ec.generate_private_key(ec.SECP256R1())
        cls.rotated = ec.generate_private_key(ec.SECP256R1())
        cls.rsa = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.now = 1900000000
        self.tick = [10]
        self.config = SupabaseJWTConfig('https://synthetic.supabase.co', 'https://synthetic.supabase.co/auth/v1',
                                      'authenticated', 'https://synthetic.supabase.co/auth/v1/.well-known/jwks.json', ('ES256', 'RS256'))
        self.jwks = {'keys': [self.jwk(self.key, 'key-1')]}
        self.requests = []
        def respond(request):
            self.requests.append(str(request.url))
            return httpx.Response(200, json=self.jwks)
        self.transport = httpx.MockTransport(respond)
        with patch.dict(os.environ, {'APP_MODE': 'cloud', 'DEMO_API_TOKEN': 'never-a-cloud-credential-0001'}):
            self.app = create_app(f'sqlite:///{self.path/"synthetic.db"}', today=lambda: date(2026, 10, 29),
                                  local_dir=self.path, jwt_config=self.config, jwks_transport=self.transport,
                                  auth_clock=lambda: self.now)
        self.client = TestClient(self.app)
        self.verifier = SupabaseJWTVerifier(self.config, self.transport, lambda: self.now, lambda: self.tick[0])

    def tearDown(self):
        self.client.close()
        self.app.state.store.engine.dispose()
        self.temp.cleanup()

    def jwk(self, key, kid, algorithm='ES256'):
        cls = jwt.algorithms.ECAlgorithm if algorithm == 'ES256' else jwt.algorithms.RSAAlgorithm
        return {**json.loads(cls.to_jwk(key.public_key())), 'kid': kid, 'alg': algorithm, 'use': 'sig'}

    def token(self, owner='owner-A', overrides=None, key=None, headers=None, algorithm='ES256'):
        payload = {'iss': self.config.issuer, 'aud': self.config.audience, 'exp': self.now+3600, 'iat': self.now-1, 'sub': owner}
        payload.update(overrides or {})
        return jwt.encode(payload, key or self.key, algorithm=algorithm, headers={'kid': 'key-1', **(headers or {})})

    def auth(self, owner='owner-A'):
        return {'Authorization': 'Bearer '+self.token(owner)}

    def call(self, method, path, owner='owner-A', body=None, key='same-command-key-0001'):
        return self.client.request(method, path, headers={**self.auth(owner), 'Idempotency-Key': key}, json=body)

    def rejected(self, token, status=401):
        with self.assertRaises(HTTPException) as caught:
            self.verifier.owner('Bearer '+token)
        self.assertEqual(caught.exception.status_code, status)
        self.assertNotIn(token, caught.exception.detail)

    def test_valid_es256_rsa_and_trusted_jwks_cache(self):
        self.assertEqual(self.verifier.owner('Bearer '+self.token()), 'owner-A')
        self.assertEqual(self.verifier.owner('Bearer '+self.token('owner-B')), 'owner-B')
        self.assertEqual(self.requests, [self.config.jwks_url])
        self.jwks = {'keys': [self.jwk(self.rsa, 'rsa-key', 'RS256')]}
        self.tick[0] += 2
        self.assertEqual(self.verifier.owner('Bearer '+self.token(key=self.rsa, headers={'kid': 'rsa-key'}, algorithm='RS256')), 'owner-A')
        self.assertEqual(self.requests, [self.config.jwks_url]*2)

    def test_claim_signature_and_algorithm_validation(self):
        for overrides in ({'iss': 'https://evil.example'}, {'aud': 'foreign'}, {'exp': self.now}, {'exp': '1900001000'},
                          {'exp': True}, {'sub': ''}, {'sub': 123}, {'sub': 'local-demo'}, {'nbf': self.now+10}, {'iat': self.now+10}):
            with self.subTest(overrides=overrides):
                self.rejected(self.token(overrides=overrides))
        self.rejected(self.token(key=self.rotated))
        self.rejected(jwt.encode({'sub': 'owner-A'}, 'synthetic-secret-not-a-trusted-key', algorithm='HS256', headers={'kid': 'key-1'}))
        self.rejected(jwt.encode({'sub': 'owner-A'}, '', algorithm='none', headers={'kid': 'key-1'}))
        for missing in ('sub', 'exp', 'aud', 'iss'):
            claims = {'iss': self.config.issuer, 'aud': 'authenticated', 'exp': self.now+100, 'sub': 'owner-A'}
            del claims[missing]
            self.rejected(jwt.encode(claims, self.key, algorithm='ES256', headers={'kid': 'key-1'}))

    def test_token_cannot_select_key_url_or_embedded_key(self):
        for headers in ({'jku': 'https://evil.example/keys'}, {'x5u': 'https://evil.example/cert'},
                        {'jwk': self.jwk(self.rotated, 'evil')}, {'crit': ['unknown']}):
            self.rejected(self.token(headers=headers))
        self.assertEqual(self.requests, [])

    def test_rotation_unknown_key_and_refresh_cooldown(self):
        self.verifier.owner('Bearer '+self.token())
        self.rejected(self.token(headers={'kid': 'unknown'}))
        self.assertEqual(len(self.requests), 1)
        self.tick[0] += 2
        self.jwks = {'keys': [self.jwk(self.rotated, 'rotated')]}
        self.assertEqual(self.verifier.owner('Bearer '+self.token(key=self.rotated, headers={'kid': 'rotated'})), 'owner-A')
        self.rejected(self.token(headers={'kid': 'unresolved'}))
        self.assertEqual(len(self.requests), 2)
        self.tick[0] += 601
        self.verifier.owner('Bearer '+self.token(key=self.rotated, headers={'kid': 'rotated'}))
        self.assertEqual(len(self.requests), 3)

    def test_provider_failure_is_sanitized_503_and_bounded(self):
        def failing(request):
            self.requests.append(str(request.url))
            raise httpx.ConnectError('provider private diagnostic', request=request)
        self.verifier.transport = httpx.MockTransport(failing)
        self.rejected(self.token(), 503)
        self.rejected(self.token(), 503)
        self.assertEqual(len(self.requests), 1)

    def test_provider_redirect_and_oversize_keys_never_follow_or_accept(self):
        for response in (httpx.Response(302, headers={'Location': 'https://evil.example/keys'}),
                         httpx.Response(200, content=b' '*65537)):
            requests = []
            def reply(request):
                requests.append(str(request.url))
                return response
            verifier = SupabaseJWTVerifier(self.config, httpx.MockTransport(reply), lambda: self.now)
            with self.assertRaises(HTTPException) as caught:
                verifier.owner('Bearer '+self.token())
            self.assertEqual(caught.exception.status_code, 503)
            self.assertEqual(requests, [self.config.jwks_url])

    def test_malformed_jwks_rejected(self):
        for keys in ([], [self.jwk(self.key, 'same'), self.jwk(self.rotated, 'same')], [{'kid': 'unsupported', 'kty': 'oct', 'k': 'secret'}]):
            with self.subTest(keys=keys):
                self.jwks = {'keys': keys}
                verifier = SupabaseJWTVerifier(self.config, self.transport, lambda: self.now)
                with self.assertRaises(HTTPException) as caught:
                    verifier.owner('Bearer '+self.token())
                self.assertEqual(caught.exception.status_code, 503)

    def test_all_api_readers_require_valid_identity_no_cloud_local_fallback(self):
        for path in ('/v1/state', '/v1/export', '/v2/personal', '/v2/planning', '/v2/frontend', '/v2/assistant/context', '/v2/observations', '/v1/transactions', '/v1/lessons'):
            for authorization in (None, 'Bearer never-a-cloud-credential-0001', 'bad', 'Bearer bad.token.value', 'Bearer  token'):
                response = self.client.get(path, headers={'Authorization': authorization} if authorization else {})
                self.assertEqual(response.status_code, 401, path)
        self.assertEqual(self.client.get('/health').json()['mode'], 'cloud')

    def test_api_owner_isolation_account_spoof_export_delete(self):
        account_body = {'revision': 0, 'name': 'Synthetic', 'currency': 'EUR', 'balance': 100000, 'confirmed_on': '2026-10-29'}
        first = self.call('POST', '/v2/accounts', body=account_body)
        second = self.call('POST', '/v2/accounts', 'owner-B', {**account_body, 'balance': 200000})
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        aid = first.json()['data']['accounts'][0]['id']
        before_a = self.call('GET', '/v1/export').json()
        before_b = self.call('GET', '/v1/export', 'owner-B').json()
        foreign = self.call('PUT', f'/v2/accounts/{aid}/balance', 'owner-B', {'revision': 1, 'balance': 1, 'confirmed_on': '2026-10-29'}, 'foreign-balance-key')
        self.assertEqual(foreign.status_code, 422)
        spoof = self.call('POST', '/v2/accounts', 'owner-B', {**account_body, 'revision': 1, 'user_id': 'owner-A'}, 'spoof-owner-key-0001')
        self.assertEqual(spoof.status_code, 422)
        self.assertEqual(self.call('GET', '/v1/export').json(), before_a)
        self.assertEqual(self.call('GET', '/v1/export', 'owner-B').json(), before_b)
        self.assertEqual(self.call('DELETE', '/v1/data').status_code, 200)
        self.assertEqual(self.call('GET', '/v1/export', 'owner-B').json(), before_b)
        self.assertEqual(self.call('GET', '/v2/personal').json()['data']['accounts'], [])

    def test_store_all_five_tables_same_ids_receipts_and_erase(self):
        store = self.app.state.store
        for owner, value in [('owner-A', 'A'), ('owner-B', 'B')]:
            store.mutate(owner, 'shared-key', 0, {'kind': 'synthetic', 'value': value}, lambda state: None, lambda state: {'owner': value})
            store.save_preview(owner, 'shared-id', 'preview-'+value)
            store.save_run(owner, 'shared-id', 1, 'ready', 'run-'+value)
            store.publish_atomic(owner, 'shared-id', 'shared-id', 1, lambda: 'run-published-'+value, json.dumps({'owner': value}))
        for owner, value in [('owner-A', 'A'), ('owner-B', 'B')]:
            self.assertEqual(store.mutate(owner, 'shared-key', 0, {'kind': 'synthetic', 'value': value}, lambda state: self.fail('duplicate effect'), lambda state: {}), {'owner': value})
            self.assertEqual(store.get_preview(owner, 'shared-id'), 'preview-'+value)
            self.assertEqual(store.get_run(owner, 'shared-id'), 'run-published-'+value)
            self.assertEqual(json.loads(store.get_latest_publication(owner)), {'owner': value})
        self.assertIsNone(store.get_preview('foreign-owner', 'shared-id'))
        self.assertIsNone(store.get_run('foreign-owner', 'shared-id'))
        self.assertIsNone(store.get_publication('foreign-owner', 'shared-id'))
        store.delete_preview('owner-A', 'shared-id')
        self.assertEqual(store.get_preview('owner-B', 'shared-id'), 'preview-B')
        with self.assertRaises(Conflict):
            store.publish_atomic('owner-A', 'shared-id', 'new-pub', 0, lambda: 'bad', '{}')
        self.assertEqual(self.call('DELETE', '/v1/data').status_code, 200)
        self.assertEqual(store.read('owner-A').revision, 0)
        self.assertIsNone(store.get_run('owner-A', 'shared-id'))
        self.assertIsNone(store.get_publication('owner-A', 'shared-id'))
        self.assertEqual(store.get_run('owner-B', 'shared-id'), 'run-published-B')
        self.assertEqual(store.get_preview('owner-B', 'shared-id'), 'preview-B')
        self.assertEqual(store.mutate('owner-B', 'shared-key', 0, {'kind': 'synthetic', 'value': 'B'}, lambda state: self.fail('duplicate'), lambda state: {}), {'owner': 'B'})

    def test_foreign_import_id_cannot_be_read_or_applied(self):
        response = self.client.post('/v1/imports', headers=self.auth(), files={'file': ('synthetic.csv', b'Date,Description,Amount\n2026-10-28,SYNTHETIC,20.00\n', 'text/csv')})
        self.assertEqual(response.status_code, 200, response.text)
        preview = response.json()['id']
        self.assertEqual(self.call('GET', f'/v1/imports/{preview}', 'owner-B').status_code, 404)
        self.assertEqual(self.call('POST', f'/v2/imports/{preview}/apply', 'owner-B', {'revision': 0}).status_code, 404)
        self.assertEqual(self.call('GET', '/v1/export', 'owner-B').json()['transactions'], [])

    def test_configuration_rejected_before_storage_and_local_alias_preserved(self):
        with patch.dict(os.environ, {'APP_MODE': 'cloud'}, clear=True), patch('vela.main.Store') as store:
            with self.assertRaises(RuntimeError):
                create_app(local_dir=self.path)
            store.assert_not_called()
        with patch.dict(os.environ, {'APP_MODE': 'cloud'}, clear=True), patch('vela.main.Store') as store:
            with self.assertRaisesRegex(RuntimeError, 'explicit database'):
                create_app(local_dir=self.path, jwt_config=self.config)
            store.assert_not_called()
        for mode in ('local', 'demo'):
            with patch.dict(os.environ, {'APP_MODE': mode}):
                app = create_app(f'sqlite:///{self.path/(mode+".db")}', 'synthetic-local-token-0001', local_dir=self.path)
            try:
                with TestClient(app) as client:
                    self.assertEqual(client.get('/v2/personal', headers={'Authorization': 'Bearer synthetic-local-token-0001'}).status_code, 200)
                    self.assertEqual(client.get('/v2/personal', headers=self.auth()).status_code, 401)
            finally:
                app.state.store.engine.dispose()
        with patch.dict(os.environ, {'APP_MODE': 'production', 'APP_ENV': 'local'}), patch('vela.main.Store') as store:
            with self.assertRaises(RuntimeError):
                create_app(local_dir=self.path)
            store.assert_not_called()
        for config in (
            dict(project_url='http://synthetic.supabase.co'), dict(jwks_url='https://evil.example/keys'),
            dict(issuer='https://evil.example/auth/v1'), dict(audience=''), dict(algorithms=('HS256',)),
        ):
            with self.assertRaises(RuntimeError):
                SupabaseJWTConfig(**{**self.config.__dict__, **config})
