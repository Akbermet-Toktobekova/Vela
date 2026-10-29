"""Explicit-connection migrations; never read .env or default to a working DB."""
from alembic import context
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, pool

config = context.config


def migrate(connection):
    # sqlite3 otherwise defers BEGIN until DML: schema DDL could survive a failed
    # upgrade. Start a real transaction before validation and any version DDL.
    if connection.dialect.name == 'sqlite' and not connection.connection.dbapi_connection.in_transaction:
        connection.exec_driver_sql('BEGIN IMMEDIATE')
    # Inspect before Alembic creates its version table or applies any DDL.
    # The frozen baseline module, not mutable runtime metadata, defines adoption.
    scripts = ScriptDirectory.from_config(config)
    baseline = scripts.get_revision('0001_initial_schema').module
    from sqlalchemy import inspect, text
    names = set(inspect(connection).get_table_names())
    versions = connection.execute(text('SELECT version_num FROM alembic_version')).scalars().all() if 'alembic_version' in names else []
    if names & {'import_job', 'import_generation'} or versions == ['0003_import_jobs']:
        scripts.get_revision('0003_import_jobs').module.validate_schema(connection, baseline, scripts.get_revision('0002_private_originals').module)
    elif 'private_original' in names or versions == ['0002_private_originals']:
        scripts.get_revision('0002_private_originals').module.validate_schema(connection, baseline)
    else:
        baseline.validate_schema(connection)
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError('Offline migration SQL is disabled: schema adoption requires an inspected connection.')
elif config.attributes.get('connection') is not None:
    migrate(config.attributes['connection'])
else:
    url = context.get_x_argument(as_dictionary=True).get('database_url')
    if not url:
        raise RuntimeError('Pass an explicit -x database_url=...; no default database is selected.')
    engine = create_engine(url, poolclass=pool.NullPool)
    try:
        with engine.begin() as connection:
            migrate(connection)
    finally:
        engine.dispose()
