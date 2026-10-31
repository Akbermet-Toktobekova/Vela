"""Offline-validatable cloud launch contract. Never loads dotenv or a local DB."""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import runpy
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
API = ROOT/'services/api'
if str(API) not in sys.path:
    sys.path.insert(0, str(API))


class CloudConfigError(ValueError):
    """Contains setting names only, never their supplied values."""


def required(env, name):
    value = env.get(name, '')
    if not isinstance(value, str) or not value.strip():
        raise CloudConfigError('Set '+name+'.')
    return value


def postgres_url(value):
    try:
        parsed = urlsplit(value)
        query = parse_qs(parsed.query, keep_blank_values=True)
        if (parsed.scheme != 'postgresql+psycopg' or not parsed.hostname or not parsed.username or not parsed.password
                or not parsed.path.strip('/') or parsed.fragment or parsed.hostname in ('localhost', '127.0.0.1', '::1')
                or query.get('sslmode') != ['verify-full'] or len(query.get('sslrootcert', [])) != 1
                or any(len(values) != 1 for values in query.values())
                or set(query)-{'sslmode','sslrootcert','connect_timeout','application_name'}):
            raise ValueError()
        parsed.port
        certificate = Path(query['sslrootcert'][0])
        if not certificate.is_absolute() or not certificate.is_file():
            raise ValueError()
        return value
    except (ValueError, OSError):
        raise CloudConfigError('Use an explicit postgresql+psycopg DATABASE_URL with verify-full and an installed CA file.') from None


@dataclass(frozen=True)
class CloudConfig:
    role: str
    database_url: str = field(repr=False)
    state_dir: Path
    project_url: str
    bucket: str
    storage_key: str = field(repr=False)
    origins: tuple[str, ...]
    port: int | None
    jwt_config: object = field(repr=False)
    lease_seconds: int = 120
    heartbeat_seconds: int = 30
    max_attempts: int = 3
    backoff_seconds: int = 5

    @classmethod
    def from_env(cls, role, env=None):
        env = os.environ if env is None else env
        if role not in ('api','worker'):
            raise CloudConfigError('Choose api or worker.')
        if env.get('APP_MODE') != 'cloud':
            raise CloudConfigError('APP_MODE must be cloud.')
        if env.get('ENABLE_GEMINI','false') != 'false' or env.get('ALLOW_RAW_DOCUMENT_AI','false') != 'false':
            raise CloudConfigError('AI activation is blocked until shared quota and processing controls are independently accepted.')
        database = postgres_url(required(env,'DATABASE_URL'))
        state_dir = Path(required(env,'CLOUD_STATE_DIR'))
        if not state_dir.is_absolute():
            raise CloudConfigError('CLOUD_STATE_DIR must be an explicit absolute directory.')
        from vela.auth import SupabaseJWTConfig
        from vela.storage import SupabaseObjects
        from vela.jobs import JobConfig
        try:
            jwt = SupabaseJWTConfig(required(env,'SUPABASE_URL'),required(env,'SUPABASE_JWT_ISSUER'),
                required(env,'SUPABASE_JWT_AUDIENCE'),required(env,'SUPABASE_JWKS_URL'),
                tuple(v.strip() for v in required(env,'SUPABASE_JWT_ALGORITHMS').split(',') if v.strip()))
            bucket, key = required(env,'SUPABASE_STORAGE_BUCKET'), required(env,'SUPABASE_STORAGE_SERVICE_KEY')
            SupabaseObjects(jwt.project_url,bucket,key)  # Constructor validation only; no request.
            values = [int(env.get(name, default)) for name,default in (
                ('JOB_LEASE_SECONDS',120),('JOB_HEARTBEAT_SECONDS',30),('JOB_MAX_ATTEMPTS',3),('JOB_BACKOFF_SECONDS',5))]
            JobConfig(*values)
        except CloudConfigError:
            raise
        except (RuntimeError,ValueError,TypeError):
            raise CloudConfigError('Check Supabase trusted settings and positive job timing configuration.') from None
        origins = ()
        port = None
        if role == 'api':
            try:
                supplied = json.loads(required(env,'FRONTEND_ORIGINS'))
                if not isinstance(supplied,list) or any(not isinstance(origin,str) for origin in supplied):raise ValueError()
                for origin in supplied:
                    parsed = urlsplit(origin)
                    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
                            or parsed.path or parsed.query or parsed.fragment or '*' in origin):raise ValueError()
                    parsed.port
                origins = tuple(dict.fromkeys(supplied))
                port = int(required(env,'PORT'))
                if not 1024 <= port <= 65535 or port in (8000,8001,8002,8003):raise ValueError()
            except CloudConfigError:
                raise
            except (ValueError,TypeError):
                raise CloudConfigError('Set PORT to an allowed explicit port and FRONTEND_ORIGINS to exact HTTPS origins (JSON list).') from None
        return cls(role,database,state_dir,jwt.project_url,bucket,key,origins,port,jwt,*values)


def launch(config, *, once=False):
    # The launcher cannot enable paid AI while each process owns SQLite quotas.
    os.environ['APP_MODE'] = 'cloud'
    os.environ['ENABLE_GEMINI'] = 'false'
    os.environ['ALLOW_RAW_DOCUMENT_AI'] = 'false'
    os.environ['SUPABASE_STORAGE_SERVICE_KEY'] = config.storage_key
    if config.role == 'api':
        import uvicorn
        def factory():
            from vela.main import create_app
            from vela.storage import SupabaseObjects
            from vela.jobs import JobConfig
            objects = SupabaseObjects(config.project_url,config.bucket,config.storage_key)
            app = create_app(database_url=config.database_url,local_dir=config.state_dir,storage_objects=objects,
                             frontend_origins=list(config.origins),jwt_config=config.jwt_config)
            # Route closures reference this repository; share the same explicit
            # enqueue lease settings as the separately launched worker.
            app.state.jobs.config = JobConfig(config.lease_seconds,config.heartbeat_seconds,
                                              config.max_attempts,config.backoff_seconds)
            return app
        uvicorn.run(factory,factory=True,host='0.0.0.0',port=config.port,access_log=False)
        return
    # Adapt the existing CLI in-process. The DB password never becomes an OS
    # process command-line argument; do not print or log this internal argv.
    previous = sys.argv
    try:
        sys.argv = [str(ROOT/'scripts/run-worker.py'),'--database-url',config.database_url,'--mode','cloud',
            '--project-url',config.project_url,'--bucket',config.bucket,'--quota-dir',str(config.state_dir),
            '--lease-seconds',str(config.lease_seconds),'--heartbeat-seconds',str(config.heartbeat_seconds),
            '--max-attempts',str(config.max_attempts),'--backoff-seconds',str(config.backoff_seconds)]
        if once:sys.argv.append('--once')
        runpy.run_path(str(ROOT/'scripts/run-worker.py'),run_name='__main__')
    finally:
        sys.argv = previous


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role',choices=('api','worker'))
    parser.add_argument('--check-config',action='store_true')
    parser.add_argument('--once',action='store_true',help='Worker only.')
    args = parser.parse_args(argv)
    try:
        config = CloudConfig.from_env(args.role)
        if args.once and args.role != 'worker':raise CloudConfigError('--once is worker-only.')
        if args.check_config:
            print('Cloud configuration shape checked offline; provider/TLS/RLS/activation remain unverified. No network contacted.')
        else:
            launch(config,once=args.once)
        return 0
    except CloudConfigError as error:
        print(str(error),file=sys.stderr)
        return 2
    except Exception:
        print('Cloud service unavailable. Check its configuration and retry.',file=sys.stderr)
        return 1
