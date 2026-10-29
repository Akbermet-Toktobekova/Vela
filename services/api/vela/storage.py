"""Private originals with durable retention/deletion metadata; no import effects."""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from fastapi import Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

RETENTION_SECONDS = 30*24*60*60
MAX_BYTES = 16*1024*1024


class StorageUnavailable(Exception):
    """Generic availability failure; no provider response/keys/filename attached."""


@dataclass(frozen=True)
class StoredFile:
    file_id: str
    sha256: str
    size: int
    created_at: int
    expires_at: int


def file_identity(owner, file_id):
    if not isinstance(owner, str) or not owner or len(owner) > 128 or any(c in owner for c in ('..', '/', '\\', '\x00')):
        raise ValueError('Invalid owner identity.')
    if not isinstance(file_id, str) or re.fullmatch(r'[0-9a-f]{32}', file_id) is None:
        raise ValueError('Invalid original identity.')
    return hashlib.sha256(owner.encode()).hexdigest() + '/' + file_id


class LocalObjects:
    name = 'local'

    def __init__(self, root):
        self.root = Path(root)
        if self.root.is_symlink():
            raise ValueError('Storage root cannot be a symlink.')
        self.root.mkdir(parents=True, exist_ok=True)
        self.root = self.root.resolve()
        self.identity = 'local:'+hashlib.sha256(str(self.root).encode()).hexdigest()

    def path(self, key):
        if re.fullmatch(r'[0-9a-f]{64}/[0-9a-f]{32}', key) is None:
            raise ValueError('Invalid object identity.')
        path = self.root / key
        if path.parent.is_symlink() or path.is_symlink() or path.resolve().parent.parent != self.root:
            raise ValueError('Object escapes private storage.')
        return path

    def put(self, key, data):
        path = self.path(key)
        path.parent.mkdir(exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)

    def get(self, key):
        try:
            with self.path(key).open('rb') as stream:
                return stream.read(MAX_BYTES+1)
        except FileNotFoundError:
            raise StorageUnavailable() from None

    def delete(self, key):
        self.path(key).unlink(missing_ok=True)


class SupabaseObjects:
    name = 'supabase'

    def __init__(self, project_url, bucket, service_key, transport=None):
        origin = urlsplit(project_url)
        if origin.scheme != 'https' or not origin.hostname or origin.username or origin.password or origin.path or origin.query or origin.fragment:
            raise RuntimeError('Configure a trusted Supabase HTTPS origin for private storage.')
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,62}', bucket or '') or not service_key or '\n' in service_key or '\r' in service_key:
            raise RuntimeError('Configure the private bucket and backend-only storage key.')
        self.base, self.bucket, self.key, self.transport = project_url+'/storage/v1', bucket, service_key, transport
        self.identity = 'supabase:'+hashlib.sha256((self.base+'\x00'+self.bucket).encode()).hexdigest()

    def request(self, method, path, data=None):
        try:
            with httpx.Client(transport=self.transport, timeout=5, follow_redirects=False, trust_env=False) as client:
                with client.stream(method, self.base+path,
                    headers={'Authorization': 'Bearer '+self.key, 'apikey': self.key,
                             'Content-Type': 'application/octet-stream', 'x-upsert': 'false'}, content=data) as response:
                    if method == 'DELETE' and response.status_code == 404:
                        return b''
                    response.raise_for_status()
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise StorageUnavailable()
                    return bytes(body)
        except (httpx.HTTPError, ValueError):
            raise StorageUnavailable() from None

    def private_bucket(self):
        import json
        try:
            record = json.loads(self.request('GET', '/bucket/'+self.bucket))
            if record.get('id') != self.bucket or record.get('public') is not False:
                raise StorageUnavailable()
        except (ValueError, TypeError, AttributeError):
            raise StorageUnavailable() from None

    def put(self, key, data):
        self.private_bucket()
        self.request('POST', '/object/'+self.bucket+'/'+key, data)

    def get(self, key):
        self.private_bucket()
        return self.request('GET', '/object/authenticated/'+self.bucket+'/'+key)

    def delete(self, key):
        self.request('DELETE', '/object/'+self.bucket+'/'+key)


class PrivateStorage:
    def __init__(self, store, objects, clock=None):
        self.store, self.objects = store, objects
        self.clock = clock or time.time

    def save_file(self, user_id, filename, data, *, retention_consent=False, _file_id=None):
        if retention_consent is not True:
            raise ValueError('Explicit consent to retain this original for 30 days is required.')
        if (not isinstance(filename, str) or not filename or len(filename) > 180
                or any(c in filename for c in ('..', '/', '\\', '\x00')) or any(ord(c) < 32 for c in filename)):
            raise ValueError('Invalid original filename.')
        if not isinstance(data, bytes) or not data or len(data) > MAX_BYTES:
            raise ValueError('Original must contain at most16MiB of bytes.')
        file_id, now = _file_id or uuid4().hex, int(self.clock())
        key = file_identity(user_id, file_id)
        digest = hashlib.sha256(data).hexdigest()
        values = dict(backend=self.objects.identity, object_key=key, sha256=digest,
                      size=len(data), created_at=now, expires_at=now+RETENTION_SECONDS)
        # Before external I/O, persist cleanup intent even if upload response is lost.
        with self.store.lock:
            if self.store.get_original(user_id, file_id) is not None:
                raise ValueError('An original identity cannot be reused.')
            self.store.add_original(user_id, file_id, **values, status='pending')
            cleanup_confirmed = False
            try:
                self.objects.put(key, data)
                if not self.store.activate_original(user_id, file_id):
                    # Another Store/process deleted this upload while I/O ran.
                    # Re-establish durable intent BEFORE compensating deletion.
                    self.store.original_cleanup_intent(user_id, file_id, **values)
                    cleanup_confirmed = self.erase_file(user_id, file_id)
                    raise StorageUnavailable()
            except (StorageUnavailable, OSError, ValueError):
                if not cleanup_confirmed:
                    self.store.original_cleanup_intent(user_id, file_id, **values)
                raise StorageUnavailable() from None
        return StoredFile(file_id, digest, len(data), now, now+RETENTION_SECONDS)

    def metadata(self, user_id, file_id):
        key = file_identity(user_id, file_id)
        row = self.store.get_original(user_id, file_id)
        if row is None:
            raise FileNotFoundError('Original not found.')
        if row['object_key'] != key or row['backend'] != self.objects.identity:
            raise StorageUnavailable()
        return row

    def read_file(self, user_id, file_id):
        with self.store.lock:
            row = self.metadata(user_id, file_id)
            if row['status'] != 'ready' or int(self.clock()) >= row['expires_at']:
                raise FileNotFoundError('Original unavailable or expired.')
            data = self.objects.get(row['object_key'])
            if len(data) != row['size'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise ValueError('Integrity check failed')
            return data

    def erase_file(self, user_id, file_id):
        with self.store.lock:
            try:
                row = self.metadata(user_id, file_id)
            except FileNotFoundError:
                return True
            except StorageUnavailable:
                self.store.original_status(user_id, file_id, 'delete_pending')
                return False
            self.store.original_status(user_id, file_id, 'delete_pending')
            try:
                self.objects.delete(row['object_key'])
            except (StorageUnavailable, OSError, ValueError):
                return False
            self.store.remove_original(user_id, file_id)
            return True

    def erase_user_files(self, user_id):
        pending = 0
        with self.store.lock:
            for row in self.store.list_originals(user_id):
                if not self.erase_file(user_id, row['file_id']):
                    pending += 1
        return pending

    def cleanup(self):
        """Internal worker hook; caller schedules it, no public erase-all endpoint."""
        pending = 0
        for row in self.store.list_originals():
            if row['status'] != 'ready' or int(self.clock()) >= row['expires_at']:
                pending += not self.erase_file(row['owner'], row['file_id'])
        return pending

    def erase_all(self, *, disposable=False):
        if disposable is not True or self.objects.name != 'local':
            raise ValueError('Erase-all is limited to explicitly disposable local tests.')
        return sum(self.erase_user_files(owner) for owner in {r['owner'] for r in self.store.list_originals()})


class OriginalDeletion(BaseModel):
    status: str


def install_storage(app, storage, owner):
    @app.get('/v2/originals/{file_id}', response_class=Response)
    def read_original(file_id: str, who=Depends(owner)):
        try:
            return Response(storage.read_file(who, file_id), media_type='application/octet-stream',
                headers={'Content-Disposition': 'attachment; filename="original"', 'Cache-Control': 'no-store'})
        except (FileNotFoundError, ValueError):
            raise HTTPException(404, 'Original unavailable or expired.') from None
        except StorageUnavailable:
            raise HTTPException(503, 'Private original storage is temporarily unavailable.') from None

    @app.delete('/v2/originals/{file_id}', response_model=OriginalDeletion, responses={202: {'model': OriginalDeletion}})
    def delete_original(file_id: str, who=Depends(owner)):
        try:
            storage.metadata(who, file_id)  # Foreign IDs cannot be enumerated/deleted.
            done = storage.erase_file(who, file_id)
            return JSONResponse({'status': 'deleted' if done else 'deletion_pending'}, status_code=200 if done else 202)
        except (FileNotFoundError, ValueError):
            raise HTTPException(404, 'Original not found.') from None
        except StorageUnavailable:
            raise HTTPException(503, 'Private original storage is temporarily unavailable.') from None


def configured_objects(mode, local, project_url=None, transport=None):
    if mode != 'cloud':
        return LocalObjects(local/'storage')
    bucket, key = os.getenv('SUPABASE_STORAGE_BUCKET', ''), os.getenv('SUPABASE_STORAGE_SERVICE_KEY', '')
    if not bucket and not key:
        class UnconfiguredCloudObjects:
            name = 'supabase'
            identity = 'supabase:unconfigured'
            def put(self, key, data): raise StorageUnavailable()
            def get(self, key): raise StorageUnavailable()
            def delete(self, key): raise StorageUnavailable()
        return UnconfiguredCloudObjects()
    return SupabaseObjects(project_url or os.getenv('SUPABASE_URL', ''), bucket, key, transport)
