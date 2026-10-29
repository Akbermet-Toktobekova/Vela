"""Private originals: disposable local files/SQLite and mocked Supabase only."""
from datetime import date
import hashlib
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
import httpx
import jwt

from vela.auth import SupabaseJWTConfig
from vela.main import create_app
from vela.storage import LocalObjects, PrivateStorage, RETENTION_SECONDS, StorageUnavailable, SupabaseObjects, configured_objects
from vela.store import Store


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.url = f'sqlite:///{self.root/"synthetic.db"}'
        self.store = Store(self.url)
        self.now = [1900000000]
        self.objects = LocalObjects(self.root/'originals')
        self.storage = PrivateStorage(self.store, self.objects, lambda: self.now[0])

    def tearDown(self):
        self.store.engine.dispose()
        self.temp.cleanup()

    def save(self, owner='owner-A', data=b'synthetic bytes'):
        return self.storage.save_file(owner, 'SYNTHETIC.csv', data, retention_consent=True)

    def test_consent_before_any_bytes_or_metadata_filename_not_retained(self):
        with self.assertRaisesRegex(ValueError, 'consent'):
            self.storage.save_file('owner-A', 'SYNTHETIC.csv', b'original')
        self.assertEqual(self.store.list_originals(), [])
        self.assertEqual(list(self.objects.root.iterdir()), [])
        saved = self.save()
        row = self.store.get_original('owner-A', saved.file_id)
        self.assertNotIn('SYNTHETIC.csv', json.dumps(row))
        self.assertEqual(row['sha256'], hashlib.sha256(b'synthetic bytes').hexdigest())
        self.assertEqual(saved.expires_at-saved.created_at, RETENTION_SECONDS)
        self.assertEqual(self.storage.read_file('owner-A', saved.file_id), b'synthetic bytes')

    def test_checksum_corruption_and_original_owner_scope(self):
        saved = self.save()
        with self.assertRaises(FileNotFoundError):
            self.storage.read_file('owner-B', saved.file_id)
        row = self.store.get_original('owner-A', saved.file_id)
        self.objects.path(row['object_key']).write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'Integrity check failed'):
            self.storage.read_file('owner-A', saved.file_id)

    def test_traversal_invalid_identity_and_no_erase_all_default(self):
        for filename in ('../raw.csv', 'a/b', 'a\\b', 'a..b', '\x00', 'bad\nname'):
            with self.assertRaises(ValueError):
                self.storage.save_file('owner-A', filename, b'test', retention_consent=True)
        for owner in ('../A', 'a/b', 'a\\b', ''):
            with self.assertRaises(ValueError):
                self.save(owner)
        for file_id in ('../secret', 'A'*32, 'a/b'):
            with self.assertRaises(ValueError):
                self.storage.read_file('owner-A', file_id)
        with self.assertRaises(ValueError):
            self.storage.erase_all()
        self.assertEqual(self.store.list_originals(), [])

    def test_exact_expiry_denies_before_provider_read_and_cleanup(self):
        saved = self.save()
        self.now[0] = saved.expires_at
        with patch.object(self.objects, 'get', side_effect=AssertionError('expired provider read')):
            with self.assertRaises(FileNotFoundError):
                self.storage.read_file('owner-A', saved.file_id)
        self.assertEqual(self.storage.cleanup(), 0)
        self.assertIsNone(self.store.get_original('owner-A', saved.file_id))

    def test_delete_failure_denies_and_survives_state_erase_restart_retry(self):
        first, second = self.save(), self.save('owner-B')
        with patch.object(self.objects, 'delete', side_effect=OSError('synthetic failure')):
            self.assertEqual(self.storage.erase_user_files('owner-A'), 1)
        self.store.erase('owner-A')
        row = self.store.get_original('owner-A', first.file_id)
        self.assertEqual(row['status'], 'delete_pending')
        with self.assertRaises(FileNotFoundError):
            self.storage.read_file('owner-A', first.file_id)
        restarted = Store(self.url)
        try:
            storage = PrivateStorage(restarted, self.objects, lambda: self.now[0])
            self.assertEqual(storage.cleanup(), 0)
            self.assertIsNone(restarted.get_original('owner-A', first.file_id))
            self.assertEqual(storage.read_file('owner-B', second.file_id), b'synthetic bytes')
        finally:
            restarted.engine.dispose()

    def test_lost_upload_response_retains_durable_cleanup_intent(self):
        original_put = self.objects.put
        def lost(key, data):
            original_put(key, data)
            raise StorageUnavailable()
        with patch.object(self.objects, 'put', side_effect=lost):
            with self.assertRaises(StorageUnavailable):
                self.save()
        row = self.store.list_originals()[0]
        self.assertEqual(row['status'], 'delete_pending')
        self.assertTrue(self.objects.path(row['object_key']).exists())
        with self.assertRaises(FileNotFoundError):
            self.storage.read_file('owner-A', row['file_id'])
        self.assertEqual(self.storage.cleanup(), 0)
        self.assertFalse(self.objects.path(row['object_key']).exists())

    def test_second_store_delete_during_upload_cannot_return_ready_or_lose_retry(self):
        second = Store(self.url)
        started, release = Event(), Event()
        original_put, original_delete = self.objects.put, self.objects.delete
        fail_compensation = [False]
        def blocked_put(key, data):
            started.set()
            if not release.wait(10):
                raise AssertionError('Synthetic coordinator timeout')
            original_put(key, data)
        def delete(key):
            if fail_compensation[0]: raise OSError('Synthetic compensation failure')
            original_delete(key)
        try:
            other = PrivateStorage(second, self.objects, lambda: self.now[0])
            with patch.object(self.objects, 'put', side_effect=blocked_put), patch.object(self.objects, 'delete', side_effect=delete), ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.save)
                self.assertTrue(started.wait(10))
                self.assertEqual(other.erase_user_files('owner-A'), 0)
                self.assertEqual(second.list_originals('owner-A'), [])
                fail_compensation[0] = True
                release.set()
                with self.assertRaises(StorageUnavailable): future.result(10)
            row = second.list_originals('owner-A')[0]
            self.assertEqual(row['status'], 'delete_pending')
            with self.assertRaises(FileNotFoundError): other.read_file('owner-A', row['file_id'])
            self.assertTrue(self.objects.path(row['object_key']).exists())
            self.assertEqual(other.cleanup(), 0)
            self.assertEqual(second.list_originals('owner-A'), [])
        finally:
            release.set()
            second.engine.dispose()

    def test_pending_never_read_and_expired_failure_retries(self):
        saved = self.save()
        with self.store.engine.begin() as connection:
            from sqlalchemy import text
            connection.execute(text("UPDATE private_original SET status='pending' WHERE owner='owner-A'"))
        with self.assertRaises(FileNotFoundError):
            self.storage.read_file('owner-A', saved.file_id)
        self.now[0] += RETENTION_SECONDS
        with patch.object(self.objects, 'delete', side_effect=OSError('failure')):
            self.assertEqual(self.storage.cleanup(), 1)
        self.assertEqual(self.store.get_original('owner-A', saved.file_id)['status'], 'delete_pending')
        self.assertEqual(self.storage.cleanup(), 0)

    def test_metadata_key_tampering_never_reads_other_path(self):
        saved, foreign = self.save(), self.save('owner-B')
        from sqlalchemy import text
        foreign_key = self.store.get_original('owner-B', foreign.file_id)['object_key']
        with self.store.engine.begin() as connection:
            connection.execute(text('UPDATE private_original SET object_key=:key WHERE owner=:owner'), {'key': foreign_key, 'owner': 'owner-A'})
        with self.assertRaises(StorageUnavailable):
            self.storage.read_file('owner-A', saved.file_id)
        self.assertEqual(self.storage.erase_user_files('owner-A'), 1)
        self.assertEqual(self.storage.read_file('owner-B', foreign.file_id), b'synthetic bytes')

    def test_restart_target_change_denies_and_retains_cleanup_intent(self):
        saved = self.save()
        row = self.store.get_original('owner-A', saved.file_id)
        original_path = self.objects.path(row['object_key'])
        changed = PrivateStorage(self.store, LocalObjects(self.root/'different-root'), lambda: self.now[0])
        with self.assertRaises(StorageUnavailable): changed.read_file('owner-A', saved.file_id)
        self.assertEqual(changed.erase_user_files('owner-A'), 1)
        self.assertTrue(original_path.exists())
        self.assertEqual(self.store.get_original('owner-A', saved.file_id)['status'], 'delete_pending')
        self.assertEqual(self.storage.cleanup(), 0)
        self.assertFalse(original_path.exists())

    def test_cloud_target_bucket_origin_fingerprints_are_bound_without_secret(self):
        first = SupabaseObjects('https://synthetic.supabase.co', 'bucket-a', 'key-one')
        rotated_secret = SupabaseObjects('https://synthetic.supabase.co', 'bucket-a', 'key-two')
        changed_bucket = SupabaseObjects('https://synthetic.supabase.co', 'bucket-b', 'key-one')
        changed_origin = SupabaseObjects('https://other.supabase.co', 'bucket-a', 'key-one')
        self.assertEqual(first.identity, rotated_secret.identity)
        self.assertNotEqual(first.identity, changed_bucket.identity)
        self.assertNotEqual(first.identity, changed_origin.identity)
        self.assertNotIn('key-one', first.identity)

    def test_populated_originals_downgrade_refused_preserves_baseline(self):
        saved = self.save()
        config = Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'))
        with self.assertRaisesRegex(RuntimeError, 'disposable'):
            with self.store.engine.begin() as connection:
                config.attributes['connection'] = connection
                command.downgrade(config, '0001_initial_schema')
        self.assertEqual(self.storage.read_file('owner-A', saved.file_id), b'synthetic bytes')

    def test_api_account_delete_honest_retry_and_no_public_access(self):
        with patch.dict(os.environ, {'APP_MODE': 'local'}):
            app = create_app(self.url, 'synthetic-local-token-0001', local_dir=self.root/'app', storage_objects=self.objects, storage_clock=lambda: self.now[0])
        try:
            saved = app.state.storage.save_file('local-demo', 'private.csv', b'private', retention_consent=True)
            auth = {'Authorization': 'Bearer synthetic-local-token-0001'}
            with TestClient(app) as client:
                self.assertEqual(client.get('/v2/originals/'+saved.file_id).status_code, 401)
                read = client.get('/v2/originals/'+saved.file_id, headers=auth)
                self.assertEqual(read.content, b'private')
                self.assertEqual(read.headers['cache-control'], 'no-store')
                with patch.object(self.objects, 'delete', side_effect=OSError('provider private detail')):
                    deleted = client.delete('/v1/data', headers=auth)
                self.assertEqual(deleted.status_code, 202)
                self.assertEqual(deleted.json()['status'], 'deletion_pending')
                self.assertNotIn('provider private detail', deleted.text)
                self.assertEqual(client.get('/v2/originals/'+saved.file_id, headers=auth).status_code, 404)
                self.assertEqual(client.delete('/v1/data', headers=auth).status_code, 200)
                self.assertIsNone(app.state.store.get_original('local-demo', saved.file_id))
        finally:
            app.state.store.engine.dispose()

    def test_mock_supabase_private_bucket_wire_checksum_and_owner_delete(self):
        requests, remote = [], {}
        public = [False]
        fail_delete = [False]
        def provider(request):
            requests.append(request)
            if request.url.path == '/storage/v1/bucket/private-originals':
                return httpx.Response(200, json={'id': 'private-originals', 'public': public[0]})
            prefix = '/storage/v1/object/'
            path = request.url.path.removeprefix(prefix).removeprefix('authenticated/')
            if request.method == 'POST':
                remote[path] = request.content
                return httpx.Response(200, json={'Key': path})
            if request.method == 'DELETE':
                if fail_delete[0]: return httpx.Response(503)
                remote.pop(path, None)
                return httpx.Response(200, json={'message': 'Successfully deleted'})
            return httpx.Response(200, content=remote[path])
        objects = SupabaseObjects('https://synthetic.supabase.co', 'private-originals', 'backend-test-key-never-public', httpx.MockTransport(provider))
        storage = PrivateStorage(self.store, objects, lambda: self.now[0])
        a = storage.save_file('owner-A', 'sensitive.csv', b'cloud-A', retention_consent=True)
        b = storage.save_file('owner-B', 'sensitive.csv', b'cloud-B', retention_consent=True)
        self.assertEqual(storage.read_file('owner-A', a.file_id), b'cloud-A')
        self.assertTrue(any('/object/authenticated/' in request.url.path for request in requests))
        self.assertTrue(all('sensitive' not in str(request.url) and '/public/' not in str(request.url) and '/sign/' not in str(request.url) for request in requests))
        self.assertTrue(all(request.headers['apikey'] == 'backend-test-key-never-public' for request in requests))
        public[0] = True
        with self.assertRaises(StorageUnavailable): storage.read_file('owner-A', a.file_id)
        public[0], fail_delete[0] = False, True
        self.assertEqual(storage.erase_user_files('owner-A'), 1)
        fail_delete[0] = False
        self.assertEqual(storage.cleanup(), 0)
        self.assertEqual(storage.read_file('owner-B', b.file_id), b'cloud-B')
        self.assertEqual(len(remote), 1)

    def test_cloud_authenticated_original_route_owner_boundary(self):
        key = ec.generate_private_key(ec.SECP256R1())
        jwk = {**json.loads(jwt.algorithms.ECAlgorithm.to_jwk(key.public_key())), 'kid': 'synthetic', 'alg': 'ES256'}
        cfg = SupabaseJWTConfig('https://synthetic.supabase.co', 'https://synthetic.supabase.co/auth/v1', 'authenticated',
                                'https://synthetic.supabase.co/auth/v1/.well-known/jwks.json', ('ES256',))
        with patch.dict(os.environ, {'APP_MODE': 'cloud'}):
            app = create_app(self.url, local_dir=self.root/'cloud', jwt_config=cfg, auth_clock=lambda: self.now[0],
                jwks_transport=httpx.MockTransport(lambda request: httpx.Response(200, json={'keys': [jwk]})), storage_objects=self.objects)
        try:
            saved = app.state.storage.save_file('owner-A', 'private.csv', b'A-only', retention_consent=True)
            def auth(owner):
                token = jwt.encode({'iss': cfg.issuer, 'aud': cfg.audience, 'exp': self.now[0]+100, 'sub': owner}, key, algorithm='ES256', headers={'kid': 'synthetic'})
                return {'Authorization': 'Bearer '+token}
            with TestClient(app) as client:
                self.assertEqual(client.get('/v2/originals/'+saved.file_id, headers=auth('owner-B')).status_code, 404)
                self.assertEqual(client.delete('/v2/originals/'+saved.file_id, headers=auth('owner-B')).status_code, 404)
                self.assertEqual(client.get('/v2/originals/'+saved.file_id, headers=auth('owner-A')).content, b'A-only')
                self.assertEqual(client.delete('/v2/originals/'+saved.file_id, headers=auth('owner-A')).status_code, 200)
        finally:
            app.state.store.engine.dispose()

    def test_unconfigured_cloud_has_no_local_fallback_partial_config_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            objects = configured_objects('cloud', self.root/'never-created', 'https://synthetic.supabase.co')
            self.assertEqual(objects.name, 'supabase')
            with self.assertRaises(StorageUnavailable): objects.put('key', b'data')
            self.assertFalse((self.root/'never-created').exists())
        with patch.dict(os.environ, {'SUPABASE_STORAGE_BUCKET': 'private-originals'}, clear=True):
            with self.assertRaises(RuntimeError): configured_objects('cloud', self.root/'never-created', 'https://synthetic.supabase.co')
