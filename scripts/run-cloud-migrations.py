"""Manual approved cloud migration; environment DSN never enters OS argv/output."""
import argparse
import os
from pathlib import Path
import sys
from cloud_runtime import CloudConfigError, postgres_url, required


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-config',action='store_true')
    args=parser.parse_args(argv)
    try:
        if os.getenv('APP_MODE')!='cloud':raise CloudConfigError('APP_MODE must be cloud.')
        url=postgres_url(required(os.environ,'MIGRATION_DATABASE_URL'))
        if args.check_config:
            print('Migration configuration shape checked offline; no database contacted.')
            return 0
        from sqlalchemy import create_engine,text
        from alembic import command
        from alembic.config import Config
        root=Path(__file__).resolve().parents[1]
        engine=create_engine(url)
        try:
            with engine.begin() as connection:
                connection.execute(text("SELECT pg_advisory_xact_lock(hashtext('vela-schema-migration'))"))
                config=Config(str(root/'services/api/alembic.ini'))
                config.attributes['connection']=connection
                command.upgrade(config,'head')
        finally:engine.dispose()
        print('Migration command completed; validate application and access controls before activation.')
        return 0
    except CloudConfigError as error:
        print(str(error),file=sys.stderr)
        return 2
    except Exception:
        print('Cloud migration unavailable. Preserve the database and review its configuration.',file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
