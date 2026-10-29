"""Durable import outbox, lease and owner-generation guards."""
from alembic import context, op
import sqlalchemy as sa

revision = '0003_import_jobs'
down_revision = '0002_private_originals'
branch_labels = None
depends_on = None

JOB_COLUMNS = [('owner','VARCHAR'), ('job_id','VARCHAR'), ('key','VARCHAR'), ('fingerprint','VARCHAR'),
    ('generation','VARCHAR'), ('file_id','VARCHAR'), ('version','INTEGER'), ('status','VARCHAR'),
    ('attempts','INTEGER'), ('next_attempt_at','INTEGER'), ('lease_until','INTEGER'), ('lease_token','VARCHAR'),
    ('created_at','INTEGER'), ('updated_at','INTEGER'), ('payload','TEXT')]


def validate_schema(connection, baseline, originals):
    inspector = sa.inspect(connection)
    signatures = {**baseline.SCHEMA, 'private_original': originals.SIGNATURE,
        'import_generation': ([('owner','VARCHAR',False), ('generation','VARCHAR',False)], ['owner']),
        'import_job': ([(name,kind,False) for name,kind in JOB_COLUMNS], ['owner','job_id']),
        'alembic_version': ([('version_num','VARCHAR(32)',False)], ['version_num'])}
    if set(inspector.get_table_names()) != set(signatures) or inspector.get_view_names():
        raise RuntimeError('Incompatible import-job schema: unexpected or absent tables/views.')
    for table, (signature, primary) in signatures.items():
        columns = inspector.get_columns(table)
        unique = inspector.get_unique_constraints(table)
        valid_unique = (len(unique)==1 and unique[0]['column_names']==['owner','key'] and unique[0]['name']=='uq_import_job_owner_key') if table=='import_job' else not unique
        indexes=inspector.get_indexes(table)
        # PostgreSQL reflects the physical index backing this named UNIQUE
        # separately; only its exact constraint mirror is expected schema.
        unexpected_indexes=[index for index in indexes if not (
            table=='import_job' and index.get('unique') is True
            and index.get('column_names')==['owner','key']
            and index.get('name')=='uq_import_job_owner_key'
            and index.get('duplicates_constraint')=='uq_import_job_owner_key')]
        if ([(c['name'],str(c['type']).upper(),c['nullable']) for c in columns] != signature
                or inspector.get_pk_constraint(table)['constrained_columns'] != primary or not valid_unique
                or any(c.get('default') is not None or c.get('computed') or c.get('identity') for c in columns)
                or inspector.get_foreign_keys(table) or inspector.get_check_constraints(table) or unexpected_indexes):
            raise RuntimeError('Incompatible import-job schema: columns or constraints differ.')
    if connection.dialect.name=='sqlite' and connection.execute(sa.text("SELECT 1 FROM sqlite_master WHERE type='trigger' LIMIT 1")).first():
        raise RuntimeError('Incompatible import-job schema: unexpected trigger.')
    if connection.execute(sa.text('SELECT version_num FROM alembic_version')).scalars().all()!=[revision]:
        raise RuntimeError('Unknown import-job schema revision.')


def upgrade():
    op.create_table('import_generation', sa.Column('owner',sa.String(),nullable=False),
                    sa.Column('generation',sa.String(),nullable=False), sa.PrimaryKeyConstraint('owner'))
    types = {'VARCHAR':sa.String, 'INTEGER':sa.Integer, 'TEXT':sa.Text}
    op.create_table('import_job', *(sa.Column(name,types[kind](),nullable=False) for name,kind in JOB_COLUMNS),
                    sa.PrimaryKeyConstraint('owner','job_id'), sa.UniqueConstraint('owner','key',name='uq_import_job_owner_key'))


def downgrade():
    disposable=context.config.attributes.get('disposable_test_database') is True or context.get_x_argument(as_dictionary=True).get('disposable_test')=='true'
    if not disposable:
        for table in ('import_job','import_generation'):
            if op.get_bind().execute(sa.text(f'SELECT 1 FROM {table} LIMIT 1')).first():
                raise RuntimeError('Refusing populated import-job downgrade; only disposable test data may be erased.')
    op.drop_table('import_job')
    op.drop_table('import_generation')
