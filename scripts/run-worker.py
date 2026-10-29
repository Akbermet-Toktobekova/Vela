"""Explicit durable import worker. No .env or implicit database selection."""
import argparse
import asyncio
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'services/api'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database-url',required=True)
    parser.add_argument('--mode',required=True,choices=('local','cloud'))
    parser.add_argument('--storage-root')
    parser.add_argument('--project-url')
    parser.add_argument('--bucket')
    parser.add_argument('--quota-dir',required=True)
    parser.add_argument('--once',action='store_true')
    parser.add_argument('--enable-ai',action='store_true',help='Operator opt-in; job processing consent is still required.')
    parser.add_argument('--lease-seconds',type=int,default=120)
    parser.add_argument('--heartbeat-seconds',type=int,default=30)
    parser.add_argument('--max-attempts',type=int,default=3)
    parser.add_argument('--backoff-seconds',type=int,default=5)
    args=parser.parse_args()
    from vela.ai import Quotas
    from vela.jobs import JobConfig,JobRepository
    from vela.storage import LocalObjects,PrivateStorage,SupabaseObjects
    from vela.store import Store
    from vela.worker import ImportWorker
    config=JobConfig(args.lease_seconds,args.heartbeat_seconds,args.max_attempts,args.backoff_seconds)
    if args.mode=='local':
        if not args.storage_root:parser.error('--storage-root is required in local mode')
        objects=LocalObjects(args.storage_root)
    else:
        if not args.project_url or not args.bucket:parser.error('--project-url and --bucket are required in cloud mode')
        objects=SupabaseObjects(args.project_url,args.bucket,os.getenv('SUPABASE_STORAGE_SERVICE_KEY',''))
    os.environ['ENABLE_GEMINI']='true' if args.enable_ai else 'false'
    quota_dir=Path(args.quota_dir)
    quota_dir.mkdir(parents=True,exist_ok=True)
    store=Store(args.database_url)
    try:
        repository=JobRepository(store,PrivateStorage(store,objects),config=config)
        worker=ImportWorker(repository,Quotas(quota_dir/'quota.db'))
        async def run():
            while True:
                repository.cleanup()
                processed=await worker.run_once()
                if args.once:return
                if not processed:await asyncio.sleep(config.backoff_seconds)
        asyncio.run(run())
    except KeyboardInterrupt:pass
    finally:store.engine.dispose()


def entrypoint():
    try:
        main()
        return 0
    except Exception:
        print('Import worker unavailable. Check its configuration and retry.',file=sys.stderr)
        return 1


if __name__=='__main__':sys.exit(entrypoint())
