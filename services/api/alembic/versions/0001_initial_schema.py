"""Freeze the existing five owner-keyed store tables without rewriting rows."""
from alembic import context, op
import sqlalchemy as sa

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

# Frozen signatures: name -> (ordered column/type/nullability tuples, ordered PK).
# Future revisions must not alter this baseline or import runtime metadata here.
SCHEMA = {
    'demo_state': ([('owner', 'VARCHAR', False), ('revision', 'INTEGER', False), ('payload', 'TEXT', False)], ['owner']),
    'command_receipt': ([('owner', 'VARCHAR', False), ('key', 'VARCHAR', False), ('fingerprint', 'VARCHAR', False), ('response', 'TEXT', False)], ['owner', 'key']),
    'import_preview': ([('owner', 'VARCHAR', False), ('id', 'VARCHAR', False), ('payload', 'TEXT', False)], ['owner', 'id']),
    'coordination_run': ([('owner', 'VARCHAR', False), ('run_id', 'VARCHAR', False), ('financial_revision', 'INTEGER', False), ('status', 'VARCHAR', False), ('payload', 'TEXT', False)], ['owner', 'run_id']),
    'published_recommendation': ([('owner', 'VARCHAR', False), ('publication_key', 'VARCHAR', False), ('financial_revision', 'INTEGER', False), ('payload', 'TEXT', False)], ['owner', 'publication_key']),
}


def validate_schema(connection):
    inspector = sa.inspect(connection)
    names = set(inspector.get_table_names())
    if inspector.get_view_names():
        raise RuntimeError('Unrecognized store schema: views need explicit migration review.')
    if names - set(SCHEMA) - {'alembic_version'}:
        raise RuntimeError('Unrecognized store schema: unexpected tables; no migration applied.')
    if names & set(SCHEMA) and names & set(SCHEMA) != set(SCHEMA):
        raise RuntimeError('Incomplete store schema: expected all five baseline tables; no migration applied.')
    for table in names:
        expected, primary = (SCHEMA[table] if table != 'alembic_version' else
                             ([('version_num', 'VARCHAR(32)', False)], ['version_num']))
        columns = inspector.get_columns(table)
        actual = [(column['name'], str(column['type']).upper(), column['nullable']) for column in columns]
        if actual != expected or inspector.get_pk_constraint(table)['constrained_columns'] != primary:
            raise RuntimeError(f'Incompatible store schema for {table}: columns or primary key differ; no migration applied.')
        if any(column.get('default') is not None or column.get('computed') or column.get('identity') for column in columns):
            raise RuntimeError(f'Incompatible store schema for {table}: unexpected column defaults.')
        if (inspector.get_foreign_keys(table) or inspector.get_unique_constraints(table)
                or inspector.get_check_constraints(table) or inspector.get_indexes(table)):
            raise RuntimeError(f'Incompatible store schema for {table}: unexpected constraints or indexes.')
    # SQLite trigger effects are invisible to column metadata, so reject them too.
    if connection.dialect.name == 'sqlite':
        if connection.execute(sa.text("SELECT 1 FROM sqlite_master WHERE type='trigger' LIMIT 1")).first():
            raise RuntimeError('Incompatible store schema: unexpected trigger.')
    if 'alembic_version' in names:
        versions = connection.execute(sa.text('SELECT version_num FROM alembic_version')).scalars().all()
        if versions and versions != [revision]:
            raise RuntimeError('Unknown store schema revision; use a compatible application/migration pair.')
        if versions and not (names & set(SCHEMA)):
            raise RuntimeError('Incompatible store schema: version recorded but baseline tables absent.')


def upgrade():
    connection = op.get_bind()
    validate_schema(connection)
    if set(SCHEMA).issubset(sa.inspect(connection).get_table_names()):
        # Compatible unversioned legacy DB: Alembic records revision only.
        return
    op.create_table('demo_state', sa.Column('owner', sa.String(), nullable=False),
                    sa.Column('revision', sa.Integer(), nullable=False), sa.Column('payload', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('owner'))
    op.create_table('command_receipt', sa.Column('owner', sa.String(), nullable=False),
                    sa.Column('key', sa.String(), nullable=False), sa.Column('fingerprint', sa.String(), nullable=False),
                    sa.Column('response', sa.Text(), nullable=False), sa.PrimaryKeyConstraint('owner', 'key'))
    op.create_table('import_preview', sa.Column('owner', sa.String(), nullable=False),
                    sa.Column('id', sa.String(), nullable=False), sa.Column('payload', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('owner', 'id'))
    op.create_table('coordination_run', sa.Column('owner', sa.String(), nullable=False),
                    sa.Column('run_id', sa.String(), nullable=False), sa.Column('financial_revision', sa.Integer(), nullable=False),
                    sa.Column('status', sa.String(), nullable=False), sa.Column('payload', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('owner', 'run_id'))
    op.create_table('published_recommendation', sa.Column('owner', sa.String(), nullable=False),
                    sa.Column('publication_key', sa.String(), nullable=False), sa.Column('financial_revision', sa.Integer(), nullable=False),
                    sa.Column('payload', sa.Text(), nullable=False), sa.PrimaryKeyConstraint('owner', 'publication_key'))


def downgrade():
    connection = op.get_bind()
    validate_schema(connection)
    disposable = context.config.attributes.get('disposable_test_database') is True
    disposable = disposable or context.get_x_argument(as_dictionary=True).get('disposable_test') == 'true'
    if not disposable:
        for table in SCHEMA:
            if connection.execute(sa.text(f'SELECT 1 FROM {table} LIMIT 1')).first():
                raise RuntimeError('Refusing populated downgrade: only an explicitly disposable test database may be erased.')
    for table in reversed(SCHEMA):
        op.drop_table(table)
