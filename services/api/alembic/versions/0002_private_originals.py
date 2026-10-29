"""Durable private-original retention and cleanup metadata; no financial rewrite."""
from alembic import context, op
import sqlalchemy as sa

revision = '0002_private_originals'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

SIGNATURE = ([('owner', 'VARCHAR', False), ('file_id', 'VARCHAR', False), ('backend', 'VARCHAR', False),
              ('object_key', 'VARCHAR', False), ('sha256', 'VARCHAR', False), ('size', 'INTEGER', False),
              ('created_at', 'INTEGER', False), ('expires_at', 'INTEGER', False), ('status', 'VARCHAR', False)], ['owner', 'file_id'])


def validate_schema(connection, baseline):
    inspector = sa.inspect(connection)
    expected = {**baseline.SCHEMA, 'private_original': SIGNATURE,
                'alembic_version': ([('version_num', 'VARCHAR(32)', False)], ['version_num'])}
    if set(inspector.get_table_names()) != set(expected) or inspector.get_view_names():
        raise RuntimeError('Incompatible private-original schema: unexpected or absent tables/views.')
    for table, (signature, primary) in expected.items():
        columns = inspector.get_columns(table)
        if ([(c['name'], str(c['type']).upper(), c['nullable']) for c in columns] != signature
                or inspector.get_pk_constraint(table)['constrained_columns'] != primary
                or any(c.get('default') is not None or c.get('computed') or c.get('identity') for c in columns)
                or inspector.get_foreign_keys(table) or inspector.get_unique_constraints(table)
                or inspector.get_check_constraints(table) or inspector.get_indexes(table)):
            raise RuntimeError('Incompatible private-original schema: columns or constraints differ.')
    if connection.dialect.name == 'sqlite' and connection.execute(sa.text("SELECT 1 FROM sqlite_master WHERE type='trigger' LIMIT 1")).first():
        raise RuntimeError('Incompatible private-original schema: unexpected trigger.')
    if connection.execute(sa.text('SELECT version_num FROM alembic_version')).scalars().all() != [revision]:
        raise RuntimeError('Unknown private-original schema revision.')


def upgrade():
    op.create_table('private_original',
        sa.Column('owner', sa.String(), nullable=False), sa.Column('file_id', sa.String(), nullable=False),
        sa.Column('backend', sa.String(), nullable=False), sa.Column('object_key', sa.String(), nullable=False),
        sa.Column('sha256', sa.String(), nullable=False), sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.Integer(), nullable=False), sa.Column('expires_at', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False), sa.PrimaryKeyConstraint('owner', 'file_id'))


def downgrade():
    disposable = context.config.attributes.get('disposable_test_database') is True
    disposable = disposable or context.get_x_argument(as_dictionary=True).get('disposable_test') == 'true'
    if not disposable and op.get_bind().execute(sa.text('SELECT 1 FROM private_original LIMIT 1')).first():
        raise RuntimeError('Refusing populated originals downgrade; only disposable test data may be erased.')
    op.drop_table('private_original')
