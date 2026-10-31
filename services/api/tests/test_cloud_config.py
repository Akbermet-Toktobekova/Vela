"""Cloud configuration/dispatch proofs. No sockets, providers or database connects."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import urlencode

SCRIPTS=Path(__file__).resolve().parents[3]/'scripts'
if str(SCRIPTS) not in sys.path:sys.path.insert(0,str(SCRIPTS))
from cloud_runtime import CloudConfig, CloudConfigError, launch, main


class CloudConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.ca=self.root/'synthetic-ca.crt'
        self.ca.write_text('synthetic test certificate; not a trusted real CA')
        self.env={'APP_MODE':'cloud','DATABASE_URL':'postgresql+psycopg://backend:PRIVATE_DB@db.example.invalid:5432/postgres?'+urlencode({'sslmode':'verify-full','sslrootcert':str(self.ca)}),
            'CLOUD_STATE_DIR':str(self.root/'never-created'), 'SUPABASE_URL':'https://synthetic.supabase.co',
            'SUPABASE_JWT_ISSUER':'https://synthetic.supabase.co/auth/v1','SUPABASE_JWT_AUDIENCE':'authenticated',
            'SUPABASE_JWKS_URL':'https://synthetic.supabase.co/auth/v1/.well-known/jwks.json','SUPABASE_JWT_ALGORITHMS':'ES256',
            'SUPABASE_STORAGE_BUCKET':'private-originals','SUPABASE_STORAGE_SERVICE_KEY':'PRIVATE_STORAGE',
            'FRONTEND_ORIGINS':'["https://frontend.example.invalid"]','PORT':'55198'}

    def tearDown(self):self.temp.cleanup()

    def test_check_config_is_offline_no_bind_db_or_directories_and_no_secrets(self):
        output,error=StringIO(),StringIO()
        with (patch.dict('os.environ',self.env,clear=True),patch('httpx.Client',side_effect=AssertionError('network')),
            patch('cloud_runtime.launch',side_effect=AssertionError('launch')),redirect_stdout(output),redirect_stderr(error)):
            self.assertEqual(main(['api','--check-config']),0)
        self.assertIn('shape checked offline',output.getvalue())
        self.assertNotIn('PRIVATE',output.getvalue()+error.getvalue())
        self.assertFalse((self.root/'never-created').exists())
        self.assertNotIn('PRIVATE',repr(CloudConfig.from_env('api',self.env)))

    def test_no_local_mode_database_or_port_fallback_and_no_unverified_tls(self):
        patches=[{'APP_MODE':'local'}, {'APP_MODE':''}, {'DATABASE_URL':'sqlite:///forbidden.db'},
            {'DATABASE_URL':self.env['DATABASE_URL'].replace('verify-full','require')},
            {'DATABASE_URL':self.env['DATABASE_URL']+'&host=other.invalid'},
            {'DATABASE_URL':self.env['DATABASE_URL']+'&sslmode=require'},
            {'DATABASE_URL':'postgresql+psycopg://u:p@db.invalid/postgres?sslmode=verify-full&sslrootcert=/missing/ca'},
            {'PORT':'8000'},{'PORT':'8001'},{'PORT':'8002'},{'PORT':'8003'},{'PORT':''}]
        for values in patches:
            with self.subTest(values=list(values)):
                with self.assertRaises(CloudConfigError):CloudConfig.from_env('api',{**self.env,**values})

    def test_exact_cloud_cors_and_native_only_empty_origins(self):
        for value in ('["*"]','["https://frontend.invalid/path"]','["http://frontend.invalid"]','["https://u:p@frontend.invalid"]','[1]','{}'):
            with self.assertRaises(CloudConfigError):CloudConfig.from_env('api',{**self.env,'FRONTEND_ORIGINS':value})
        self.assertEqual(CloudConfig.from_env('api',{**self.env,'FRONTEND_ORIGINS':'[]'}).origins,())
        worker_env={k:v for k,v in self.env.items() if k not in ('PORT','FRONTEND_ORIGINS')}
        self.assertIsNone(CloudConfig.from_env('worker',worker_env).port)

    def test_ai_activation_missing_or_partial_storage_and_invalid_job_settings_reject(self):
        for values in ({'ENABLE_GEMINI':'true'},{'ALLOW_RAW_DOCUMENT_AI':'true'},{'SUPABASE_STORAGE_SERVICE_KEY':''},
            {'SUPABASE_STORAGE_BUCKET':''},{'JOB_HEARTBEAT_SECONDS':'120'},{'JOB_MAX_ATTEMPTS':'0'},
            {'SUPABASE_JWKS_URL':'https://untrusted.invalid/keys'},{'SUPABASE_JWT_ALGORITHMS':'HS256'}):
            with self.assertRaises(CloudConfigError):CloudConfig.from_env('worker',{**self.env,**values})

    def test_api_dispatch_passes_explicit_db_origins_and_disables_access_logging(self):
        config=CloudConfig.from_env('api',{**self.env,'JOB_LEASE_SECONDS':'180','JOB_HEARTBEAT_SECONDS':'45',
                                               'JOB_MAX_ATTEMPTS':'4','JOB_BACKOFF_SECONDS':'7'})
        app=SimpleNamespace(state=SimpleNamespace(jobs=SimpleNamespace(config=None)))
        create=Mock(return_value=app)
        capture={}
        def fake_run(app_factory,**kwargs):capture.update(kwargs);capture['app']=app_factory()
        with patch.dict('os.environ',self.env,clear=True),patch.dict(sys.modules,{'uvicorn':SimpleNamespace(run=fake_run),'vela.main':SimpleNamespace(create_app=create)}):
            launch(config)
        self.assertEqual(create.call_args.kwargs['database_url'],self.env['DATABASE_URL'])
        self.assertEqual(create.call_args.kwargs['frontend_origins'],['https://frontend.example.invalid'])
        self.assertEqual(create.call_args.kwargs['local_dir'],self.root/'never-created')
        self.assertEqual(capture['port'],55198)
        self.assertFalse(capture['access_log'])
        self.assertTrue(capture['factory'])
        self.assertEqual(app.state.jobs.config.lease_seconds,180)
        self.assertEqual(app.state.jobs.config.heartbeat_seconds,45)
        self.assertEqual(app.state.jobs.config.max_attempts,4)
        self.assertEqual(app.state.jobs.config.backoff_seconds,7)

    def test_worker_dispatch_reuses_cli_in_process_without_secret_os_arguments_or_ai(self):
        config=CloudConfig.from_env('worker',self.env)
        original=sys.argv
        seen={}
        def fake_run(path,run_name):seen.update(path=path,args=sys.argv.copy(),name=run_name)
        with patch.dict('os.environ',self.env,clear=True),patch('cloud_runtime.runpy.run_path',side_effect=fake_run):
            launch(config,once=True)
        self.assertIs(sys.argv,original)
        self.assertEqual(seen['path'],str(SCRIPTS/'run-worker.py'))
        self.assertIn('--once',seen['args'])
        self.assertNotIn('--enable-ai',seen['args'])
        self.assertEqual(seen['args'][seen['args'].index('--mode')+1],'cloud')
        self.assertEqual(seen['args'][seen['args'].index('--database-url')+1],self.env['DATABASE_URL'])

    def test_runtime_errors_and_invalid_config_never_print_private_diagnostics(self):
        for env,raised,expected in ((self.env,RuntimeError('PRIVATE_SQL_PROVIDER_TRACE'),1),({**self.env,'DATABASE_URL':'PRIVATE_INVALID'},None,2)):
            output,error=StringIO(),StringIO()
            with patch.dict('os.environ',env,clear=True),patch('cloud_runtime.launch',side_effect=raised),redirect_stdout(output),redirect_stderr(error):
                self.assertEqual(main(['api']),expected)
            self.assertNotIn('PRIVATE',output.getvalue()+error.getvalue())
            self.assertNotIn('Traceback',error.getvalue())

    def test_templates_current_private_inventory_and_explicit_psycopg_declaration(self):
        root=SCRIPTS.parent
        template=json.loads('\n'.join((root/'deployment/render.yaml').read_text().splitlines()[1:]))
        self.assertEqual([service['type'] for service in template['services']],['web','worker'])
        for service in template['services']:
            self.assertEqual(service['autoDeployTrigger'],'off')
            env={entry['key']:entry for entry in service['envVars']}
            self.assertEqual(env['APP_MODE']['value'],'cloud')
            self.assertEqual(env['ENABLE_GEMINI']['value'],'false')
            self.assertIs(env['DATABASE_URL']['sync'],False)
            self.assertIs(env['SUPABASE_STORAGE_SERVICE_KEY']['sync'],False)
        from vela.store import metadata
        sql=(root/'deployment/deny-client-data.sql').read_text()
        array=re.search(r'expected text\[\] := ARRAY\[(.*?)\];',sql,re.S).group(1)
        inventory=set(re.findall(r"'([^']+)'",array))
        self.assertEqual(inventory,set(metadata.tables)|{'alembic_version'})
        self.assertEqual(len(inventory),9)
        self.assertIn('FROM PUBLIC, anon, authenticated',sql)
        self.assertIn('ENABLE ROW LEVEL SECURITY',sql)
        self.assertNotIn('GRANT ',sql)
        requirements=(root/'services/api/requirements.txt').read_text()
        self.assertIn('psycopg[binary]==3.3.6',requirements)


class CloudMigrationConfigTests(unittest.TestCase):
    def test_explicit_migration_config_check_is_offline_and_secret_free(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('cloud_migration_launcher',SCRIPTS/'run-cloud-migrations.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with TemporaryDirectory() as folder:
            ca=Path(folder)/'synthetic.crt';ca.write_text('not a real CA')
            env={'APP_MODE':'cloud','MIGRATION_DATABASE_URL':'postgresql+psycopg://user:PRIVATE@db.invalid/postgres?'+urlencode({'sslmode':'verify-full','sslrootcert':str(ca)})}
            output,error=StringIO(),StringIO()
            with patch.dict('os.environ',env,clear=True),patch('sqlalchemy.create_engine',side_effect=AssertionError('connect')),redirect_stdout(output),redirect_stderr(error):
                self.assertEqual(module.main(['--check-config']),0)
            self.assertNotIn('PRIVATE',output.getvalue()+error.getvalue())
            self.assertIn('no database contacted',output.getvalue())

    def test_migration_config_does_not_fall_back_to_runtime_database(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('cloud_migration_launcher',SCRIPTS/'run-cloud-migrations.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        error=StringIO()
        with patch.dict('os.environ',{'APP_MODE':'cloud','DATABASE_URL':'PRIVATE_RUNTIME'},clear=True),redirect_stderr(error):
            self.assertEqual(module.main(['--check-config']),2)
        self.assertIn('MIGRATION_DATABASE_URL',error.getvalue())
        self.assertNotIn('PRIVATE_RUNTIME',error.getvalue())
