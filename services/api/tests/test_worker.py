import asyncio
import base64
from datetime import date
import json
import io
import importlib.util
from contextlib import redirect_stdout,redirect_stderr
import os
from pathlib import Path
import subprocess
import sys
import time
from tempfile import TemporaryDirectory
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import AsyncMock,patch

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from vela.ai import AIUnavailable
from vela.imports import ImportPreview,ImportError_,build_preview
from vela.jobs import EnqueueImport,JobConfig,JobRepository
from vela.main import create_app
from vela.storage import StorageUnavailable
from vela.store import Store,Conflict
from vela.worker import ImportWorker


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.path=Path(self.temp.name)
        self.url=f'sqlite:///{self.path/"synthetic.db"}'
        self.now=[1900000000]
        with patch.dict(os.environ,{'APP_MODE':'local'}):
            self.app=create_app(self.url,'synthetic-worker-token-0001',today=lambda:date(2026,10,29),local_dir=self.path,storage_clock=lambda:self.now[0])
        self.store=self.app.state.store
        self.storage=self.app.state.storage
        self.repo=self.app.state.jobs
        self.repo.clock=lambda:self.now[0]
        self.client=TestClient(self.app)
        self.auth={'Authorization':'Bearer synthetic-worker-token-0001','Idempotency-Key':'enqueue-key-0001'}
        self.data=b'Date,Description,Amount\n2026-10-28,SYNTHETIC Salary,100.00\n'
        self.body=EnqueueImport(filename='SYNTHETIC.csv',content_type='text/csv',content_base64=base64.b64encode(self.data).decode(),retention_consent=True,
            processing={'external_ai':False,'notice_version':'import-processing-v1'})

    def tearDown(self):
        self.client.close()
        self.store.engine.dispose()
        self.temp.cleanup()

    def enqueue(self,owner='local-demo',key='enqueue-key-0001'):
        return self.repo.enqueue(owner,key,self.body)

    def preview(self,job):
        return ImportPreview(id='job-'+job['job_id'],filename='SYNTHETIC.csv',file_type='csv',parser='local')

    async def test_enqueue_retry_identity_changed_body_restart_and_analytical_preview(self):
        before=self.client.get('/v1/export',headers=self.auth).json()
        first=self.enqueue()
        second=self.enqueue()
        self.assertEqual(first,second)
        self.assertEqual(len(self.store.list_originals('local-demo')),1)
        with self.assertRaises(Conflict):
            self.repo.enqueue('local-demo','enqueue-key-0001',self.body.model_copy(update={'filename':'changed.csv'}))
        restarted=Store(self.url)
        try:
            repo=JobRepository(restarted,self.storage,clock=lambda:self.now[0])
            self.assertEqual(repo.get('local-demo',first['job_id']),first)
            worker=ImportWorker(repo,self.app.state.quotas,today=lambda:date(2026,10,29))
            await worker.run_once()
        finally:restarted.engine.dispose()
        result=self.repo.get('local-demo',first['job_id'])
        self.assertEqual(result['status'],'succeeded')
        preview=self.client.get('/v1/imports/'+result['result_preview_id'],headers=self.auth)
        self.assertEqual(preview.status_code,200,preview.text)
        self.assertEqual(preview.json()['income'],10000)
        self.assertEqual(self.client.get('/v1/export',headers=self.auth).json(),before)
        self.assertEqual(self.enqueue()['job_id'],first['job_id'])
        self.assertEqual(len(self.store.list_originals()),1)

    async def test_competing_claim_expired_lease_stale_heartbeat_and_finish(self):
        self.enqueue()
        first=self.repo.claim()
        second_store=Store(self.url)
        try:
            second=JobRepository(second_store,self.storage,clock=lambda:self.now[0])
            self.assertIsNone(second.claim())
            self.now[0]+=120
            replacement=second.claim()
            self.assertNotEqual(first['lease_token'],replacement['lease_token'])
            self.assertFalse(self.repo.heartbeat(first))
            self.assertFalse(self.repo.finish(first,self.preview(first)))
            self.assertTrue(second.heartbeat(replacement))
            self.assertTrue(second.finish(replacement,self.preview(replacement)))
            self.assertFalse(second.finish(replacement,self.preview(replacement)))
            with self.store.engine.connect() as conn:
                from vela.store import previews
                self.assertEqual(len(conn.execute(previews.select()).all()),1)
        finally:second_store.engine.dispose()

    async def test_backoff_exhaustion_permanent_and_explicit_retry_receipt(self):
        queued=self.enqueue()
        for attempt,delay in ((1,5),(2,10),(3,20)):
            job=self.repo.claim()
            self.assertEqual(job['attempts'],attempt)
            self.assertTrue(self.repo.fail(job))
            result=self.repo.get('local-demo',queued['job_id'])
            if attempt<3:
                self.assertEqual(result['next_attempt_at'],self.now[0]+delay)
                self.assertIsNone(self.repo.claim())
                self.now[0]+=delay
        self.assertEqual(result['status'],'dead_letter')
        self.assertIsNone(self.repo.claim())
        retry=self.repo.command('local-demo',queued['job_id'],'retry-key-0001',result['version'],'retry')
        self.assertEqual(retry,self.repo.command('local-demo',queued['job_id'],'retry-key-0001',result['version'],'retry'))
        with self.assertRaises(Conflict):self.repo.command('local-demo',queued['job_id'],'retry-key-0001',retry['version'],'retry')
        with self.assertRaises(Conflict):self.repo.command('local-demo',queued['job_id'],'new-stale-key',result['version'],'cancel')
        job=self.repo.claim()
        self.assertEqual(job['attempts'],1)
        self.repo.fail(job,permanent=True,code='unsupported_or_invalid_source')
        self.assertEqual(self.repo.get('local-demo',queued['job_id'])['status'],'failed')

    async def test_cancel_invalidates_running_lease_and_cannot_resurrect(self):
        queued=self.enqueue()
        job=self.repo.claim()
        current=self.repo.get('local-demo',queued['job_id'])
        cancelled=self.repo.command('local-demo',queued['job_id'],'cancel-key-0001',current['version'],'cancel')
        self.assertEqual(cancelled['status'],'cancelled')
        self.assertFalse(self.repo.finish(job,self.preview(job)))
        self.assertFalse(self.repo.heartbeat(job))
        with self.assertRaises(Conflict):self.repo.command('local-demo',queued['job_id'],'retry-new-key',cancelled['version'],'retry')
        self.assertEqual(self.enqueue()['status'],'cancelled')
        self.assertEqual(len(self.store.list_originals()),1)

    async def test_delete_owner_reenqueue_generation_and_source_expiry_guards(self):
        old=self.enqueue()
        running=self.repo.claim()
        self.store.erase('local-demo')
        fresh=self.enqueue()
        self.assertNotEqual(old['job_id'],fresh['job_id'])
        self.assertFalse(self.repo.finish(running,self.preview(running)))
        with self.assertRaises(FileNotFoundError):self.repo.get('local-demo',old['job_id'])
        current=self.repo.claim()
        row=self.store.get_original('local-demo',current['file_id'])
        self.now[0]=row['expires_at']
        self.assertFalse(self.repo.finish(current,self.preview(current)))
        self.assertIsNone(self.store.get_preview('local-demo','job-'+old['job_id']))
        self.assertIsNone(self.store.get_preview('local-demo','job-'+fresh['job_id']))

    async def test_original_only_delete_blocks_publish_without_erasing_finances(self):
        self.enqueue()
        job=self.repo.claim()
        self.storage.erase_file(job['owner'],job['file_id'])
        self.assertFalse(self.repo.finish(job,self.preview(job)))

    async def test_owner_boundary_status_commands_and_data_delete(self):
        a,b=self.enqueue('owner-A'),self.enqueue('owner-B')
        self.assertNotEqual(a['job_id'],b['job_id'])
        with self.assertRaises(FileNotFoundError):self.repo.get('owner-B',a['job_id'])
        with self.assertRaises(FileNotFoundError):self.repo.command('owner-B',a['job_id'],'foreign-key',a['version'],'cancel')
        self.store.erase('owner-A')
        self.assertEqual(self.repo.get('owner-B',b['job_id'])['job_id'],b['job_id'])
        self.assertEqual(len(self.store.list_originals('owner-B')),1)

    async def test_no_external_ai_permission_blocks_all_parser_branches(self):
        with patch('vela.imports.enabled',return_value=True),patch('vela.imports.ai_read',new=AsyncMock(side_effect=AssertionError('AI egress')) ) as read,patch(
            'vela.imports.ai_categorize',new=AsyncMock(side_effect=AssertionError('AI categorize'))) as categorize:
            await build_preview(self.data,'s.csv','text/csv',self.app.state.quotas,date(2026,10,29),'p',external_ai_allowed=False)
            for data,name,mime in ((b'bad','s.csv','text/csv'),(b'\x89PNGimage','s.png','image/png')):
                with self.assertRaises(ImportError_):await build_preview(data,name,mime,self.app.state.quotas,date(2026,10,29),'p',external_ai_allowed=False)
            with patch('vela.imports.pdf_text',return_value='unreadable extracted text '*8):
                with self.assertRaises(ImportError_):await build_preview(b'%PDFsynthetic','s.pdf','application/pdf',self.app.state.quotas,date(2026,10,29),'p',external_ai_allowed=False)
            read.assert_not_awaited();categorize.assert_not_awaited()

    async def test_worker_per_call_consent_errors_and_no_raw_diagnostics(self):
        self.enqueue()
        parser=AsyncMock(side_effect=AIUnavailable('SECRET provider diagnostic'))
        worker=ImportWorker(self.repo,self.app.state.quotas,parser=parser)
        await worker.run_once()
        self.assertIs(parser.await_args.kwargs['external_ai_allowed'],False)
        result=self.repo.get('local-demo',self.enqueue()['job_id'])
        self.assertEqual(result['status'],'retry_wait')
        self.assertNotIn('SECRET',json.dumps(result))
        self.assertNotIn('SYNTHETIC.csv',json.dumps(result))

    async def test_crash_after_upload_before_queue_recovers_same_source(self):
        self.enqueue()
        from sqlalchemy import update
        from vela.store import import_jobs
        with self.store.engine.begin() as conn:
            conn.execute(update(import_jobs).values(status='uploading',lease_until=self.now[0]+120))
        self.assertIsNone(self.repo.claim())
        self.now[0]+=120
        recovered=self.repo.claim()
        self.assertEqual(recovered['attempts'],1)
        self.assertEqual(len(self.store.list_originals()),1)

    async def test_api_ingest_consent_unique_conflict_and_no_cloud_sync_ai(self):
        for value in (1,'true',None,False):
            bad={**self.body.model_dump(),'retention_consent':value}
            self.assertEqual(self.client.post('/v1/imports/jobs',headers=self.auth,json=bad).status_code,422)
        self.assertEqual(self.client.post('/v1/imports/jobs',json=self.body.model_dump()).status_code,401)
        first=self.client.post('/v1/imports/jobs',headers=self.auth,json=self.body.model_dump())
        self.assertEqual(first.status_code,202,first.text)
        retry=self.client.post('/v1/imports/jobs',headers=self.auth,json=self.body.model_dump())
        self.assertEqual(first.json(),retry.json())
        error=IntegrityError('synthetic unique collision',{},Exception('private SQL diagnostic'))
        with patch.object(self.repo,'enqueue',side_effect=error):
            response=self.client.post('/v1/imports/jobs',headers=self.auth,json=self.body.model_dump())
            unresolved=self.client.post('/v1/imports/jobs',headers={**self.auth,'Idempotency-Key':'other-owner-gen-race'},json=self.body.model_dump())
        self.assertEqual(response.status_code,202)
        self.assertEqual(response.json()['job_id'],first.json()['job_id'])
        self.assertEqual(unresolved.status_code,409)
        self.assertNotIn('private SQL',response.text)
        self.assertEqual(self.client.delete('/v1/data',headers=self.auth).status_code,200)
        self.assertEqual(self.client.get(first.json()['status_url'],headers=self.auth).status_code,404)

    async def test_cli_explicit_database_required_and_once_offline(self):
        script=Path(__file__).resolve().parents[3]/'scripts/run-worker.py'
        missing=subprocess.run([sys.executable,str(script),'--once'],capture_output=True,text=True)
        self.assertNotEqual(missing.returncode,0)
        self.assertIn('--database-url',missing.stderr)
        self.now[0]=int(time.time())
        self.enqueue()
        result=subprocess.run([sys.executable,str(script),'--database-url',self.url,'--mode','local','--storage-root',str(self.storage.objects.root),
            '--quota-dir',str(self.path/'workerquota'),'--once'],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        # CLI and fixture use the same real UTC enqueue time for scheduling.
        self.assertEqual(self.repo.get('local-demo',self.enqueue()['job_id'])['status'],'succeeded')

    async def test_job_operational_configuration_validation(self):
        for values in ({'lease_seconds':0},{'heartbeat_seconds':120},{'max_attempts':True},{'backoff_seconds':-1}):
            with self.assertRaises(ValueError):JobConfig(**values)

    async def test_upload_intent_survives_crash_before_bytes_without_reupload_on_retry(self):
        with patch.object(self.storage,'save_file',side_effect=SystemExit('synthetic process interruption')):
            with self.assertRaises(SystemExit):self.enqueue()
        pending=self.enqueue()
        self.assertEqual(pending['status'],'uploading')
        self.assertEqual(self.store.list_originals(),[])
        self.now[0]+=120
        self.assertIsNone(self.repo.claim())
        self.assertEqual(self.enqueue()['status'],'failed')
        self.assertEqual(self.store.list_originals(),[])

    async def test_preview_and_success_commit_atomically(self):
        from sqlalchemy.engine import Connection
        original=Connection.execute
        def fail_preview(conn,statement,*args,**kwargs):
            if getattr(getattr(statement,'table',None),'name',None)=='import_preview' and getattr(statement,'is_insert',False):
                raise RuntimeError('Synthetic publication failure')
            return original(conn,statement,*args,**kwargs)
        self.enqueue()
        job=self.repo.claim()
        with patch.object(Connection,'execute',fail_preview):
            with self.assertRaises(RuntimeError):self.repo.finish(job,self.preview(job))
        self.assertEqual(self.repo.get('local-demo',job['job_id'])['status'],'running')
        self.assertIsNone(self.store.get_preview('local-demo','job-'+job['job_id']))
        self.assertTrue(self.repo.finish(job,self.preview(job)))

    async def test_cloud_legacy_sync_without_consent_never_calls_external_ai(self):
        from cryptography.hazmat.primitives.asymmetric import ec
        import jwt,httpx
        from vela.auth import SupabaseJWTConfig
        key=ec.generate_private_key(ec.SECP256R1())
        cfg=SupabaseJWTConfig('https://synthetic.supabase.co','https://synthetic.supabase.co/auth/v1','authenticated',
            'https://synthetic.supabase.co/auth/v1/.well-known/jwks.json',('ES256',))
        jwk={**json.loads(jwt.algorithms.ECAlgorithm.to_jwk(key.public_key())),'kid':'k','alg':'ES256'}
        with patch.dict(os.environ,{'APP_MODE':'cloud'}):
            app=create_app(self.url,local_dir=self.path/'cloud',jwt_config=cfg,auth_clock=lambda:self.now[0],
                jwks_transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'keys':[jwk]})),storage_objects=self.storage.objects)
        token=jwt.encode({'sub':'owner-A','iss':cfg.issuer,'aud':'authenticated','exp':self.now[0]+100},key,algorithm='ES256',headers={'kid':'k'})
        try:
            with TestClient(app) as client,patch('vela.imports.enabled',return_value=True),patch('vela.imports.ai_read',new=AsyncMock()) as read,patch('vela.imports.ai_categorize',new=AsyncMock()) as categorize:
                auth={'Authorization':'Bearer '+token}
                multipart=client.post('/v1/imports',headers=auth,files={'file':('synthetic.csv',self.data,'text/csv')})
                encoded=client.post('/v1/imports/base64',headers=auth,json={'filename':'synthetic.csv','data_base64':base64.b64encode(self.data).decode(),'content_type':'text/csv'})
                self.assertEqual(multipart.status_code,200,multipart.text)
                self.assertEqual(encoded.status_code,200,encoded.text)
                read.assert_not_awaited();categorize.assert_not_awaited()
        finally:app.state.store.engine.dispose()

    async def test_maintenance_does_not_delete_live_enqueue_source_during_put(self):
        entered,release=Event(),Event()
        original_put=self.storage.objects.put
        def blocked(key,data):
            entered.set()
            if not release.wait(10):raise AssertionError('Synthetic upload coordinator timeout')
            original_put(key,data)
        other_store=Store(self.url)
        other_storage=type(self.storage)(other_store,self.storage.objects,lambda:self.now[0])
        other_repo=JobRepository(other_store,other_storage,clock=lambda:self.now[0])
        try:
            with patch.object(self.storage.objects,'put',side_effect=blocked),ThreadPoolExecutor(max_workers=1) as executor:
                upload=executor.submit(self.enqueue)
                self.assertTrue(entered.wait(10))
                self.assertEqual(other_store.list_originals()[0]['status'],'pending')
                self.assertEqual(other_repo.cleanup(),0)
                self.assertEqual(len(other_store.list_originals()),1)
                release.set()
                ready=upload.result(10)
            self.assertEqual(ready['status'],'queued')
            self.assertEqual(other_store.list_originals()[0]['status'],'ready')
        finally:
            release.set()
            other_store.engine.dispose()

    async def test_maintenance_stale_pending_snapshot_rechecks_ready_source(self):
        from vela.store import private_originals,import_jobs
        from sqlalchemy import update
        queued=self.enqueue()
        with self.store.engine.begin() as conn:
            conn.execute(update(private_originals).values(status='pending'))
            conn.execute(update(import_jobs).values(status='uploading',lease_until=self.now[0]+120))
        original_list=self.store.list_originals
        def completes_between_listing_and_decision():
            snapshot=original_list()
            with self.store.engine.begin() as conn:
                conn.execute(update(private_originals).values(status='ready'))
                conn.execute(update(import_jobs).values(status='queued'))
            return snapshot
        with patch.object(self.store,'list_originals',side_effect=completes_between_listing_and_decision):
            self.assertEqual(self.repo.cleanup(),0)
        source=original_list()[0]
        self.assertEqual(source['status'],'ready')
        self.assertEqual(self.storage.read_file(source['owner'],source['file_id']),self.data)

    async def test_postgres_constraint_index_mirror_allowed_other_indexes_rejected(self):
        from alembic.script import ScriptDirectory
        from alembic.config import Config
        import sqlalchemy as sa
        scripts=ScriptDirectory.from_config(Config(str(Path(__file__).resolve().parents[1]/'alembic.ini')))
        module=scripts.get_revision('0003_import_jobs').module
        baseline=scripts.get_revision('0001_initial_schema').module
        originals=scripts.get_revision('0002_private_originals').module
        with self.store.engine.connect() as conn:
            inspector=sa.inspect(conn)
            mirror={'name':'uq_import_job_owner_key','column_names':['owner','key'],'unique':True,'duplicates_constraint':'uq_import_job_owner_key'}
            class PGShape:
                def __getattr__(self,name):return getattr(inspector,name)
                def get_indexes(self,table):return [mirror] if table=='import_job' else inspector.get_indexes(table)
            with patch.object(module.sa,'inspect',return_value=PGShape()):
                module.validate_schema(conn,baseline,originals)
                mirror['duplicates_constraint']='unexpected_constraint'
                with self.assertRaisesRegex(RuntimeError,'schema'):module.validate_schema(conn,baseline,originals)

    async def test_worker_cli_sanitizes_setup_claim_cleanup_diagnostics(self):
        script=Path(__file__).resolve().parents[3]/'scripts/run-worker.py'
        spec=importlib.util.spec_from_file_location('synthetic_worker_cli',script)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        arguments=[str(script),'--database-url',self.url,'--mode','local','--storage-root',str(self.storage.objects.root),
            '--quota-dir',str(self.path/'workerquota'),'--once']
        for method in ('claim','cleanup'):
            output,error=io.StringIO(),io.StringIO()
            with (patch.object(sys,'argv',arguments),patch.object(JobRepository,method,side_effect=RuntimeError('PRIVATE SQL token secret')),
                  redirect_stdout(output),redirect_stderr(error)):
                self.assertEqual(module.entrypoint(),1)
            self.assertNotIn('PRIVATE',output.getvalue()+error.getvalue())
            self.assertNotIn('Traceback',error.getvalue())
            self.assertIn('Import worker unavailable',error.getvalue())
        with patch.object(module,'main',side_effect=RuntimeError('PRIVATE setup diagnostic')),redirect_stderr(io.StringIO()) as error:
            self.assertEqual(module.entrypoint(),1)
            self.assertNotIn('PRIVATE',error.getvalue())
