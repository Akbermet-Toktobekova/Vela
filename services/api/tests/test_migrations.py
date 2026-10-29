"""Disposable synthetic baseline migration proofs; never a working database."""
import hashlib
import json
from contextlib import closing, contextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from alembic.operations import Operations
from sqlalchemy import create_engine
from vela.store import Store


API = Path(__file__).resolve().parents[1]
TABLES = ('demo_state', 'command_receipt', 'import_preview', 'coordination_run', 'published_recommendation')
# Independent pre-migration DDL, not generated from runtime or migration metadata.
LEGACY_DDL = '''
CREATE TABLE demo_state (owner VARCHAR NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(owner));
CREATE TABLE command_receipt (owner VARCHAR NOT NULL, key VARCHAR NOT NULL, fingerprint VARCHAR NOT NULL, response TEXT NOT NULL, PRIMARY KEY(owner,key));
CREATE TABLE import_preview (owner VARCHAR NOT NULL, id VARCHAR NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(owner,id));
CREATE TABLE coordination_run (owner VARCHAR NOT NULL, run_id VARCHAR NOT NULL, financial_revision INTEGER NOT NULL, status VARCHAR NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(owner,run_id));
CREATE TABLE published_recommendation (owner VARCHAR NOT NULL, publication_key VARCHAR NOT NULL, financial_revision INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(owner,publication_key));
'''


@contextmanager
def database(path):
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            yield connection


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.db = Path(self.temp.name) / 'synthetic.db'
        self.url = f'sqlite:///{self.db}'

    def tearDown(self):
        self.temp.cleanup()

    def config(self, connection, disposable=False):
        cfg = Config(str(API / 'alembic.ini'))
        cfg.attributes['connection'] = connection
        cfg.attributes['disposable_test_database'] = disposable
        return cfg

    def migrate(self, action='upgrade', target='head', disposable=False):
        engine = create_engine(self.url)
        try:
            with engine.begin() as connection:
                getattr(command, action)(self.config(connection, disposable), target)
        finally:
            engine.dispose()

    def raw(self):
        with database(self.db) as connection:
            return {table: connection.execute(f'SELECT * FROM {table} ORDER BY 1,2').fetchall() for table in TABLES}

    def schema(self):
        with database(self.db) as connection:
            return connection.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name').fetchall()

    def seed(self, ddl=LEGACY_DDL):
        snapshot = {'nickname': 'Synthetic Álex', 'currency': 'EUR', 'as_of': '2026-10-29', 'horizon': '2026-11-28',
                    'cash': 100000, 'saved': 4000, 'protected': 10000, 'goal_target': 100000, 'goal_name': 'Reserve',
                    'obligations': [{'id': 'rent', 'label': 'Rent', 'amount': 60000, 'due': '2026-11-05', 'kind': 'rent'}],
                    'obligations_complete': True, 'debt_known': True, 'provenance': 'synthetic'}
        old = {'revision': 7, 'snapshot': snapshot,
               'actions': [{'id': 'legacy-step', 'amount': 2000, 'status': 'planned', 'created_on': '2026-10-29', 'completed_on': None}],
               'history': [{'event': 'fixture', 'revision': 7, 'source': 'synthetic'}], 'income_ids': ['original-income'],
               'deferred': False, 'transactions': [{'id': 'row-1', 'date': '2026-08-21', 'description': 'SYNTHETIC refund', 'amount': 2000, 'category': 'refunds', 'source': 'import:fixture'}], 'debts': []}
        current = json.loads(json.dumps(old))
        current['personal'] = {'focus': 'goal', 'income_type': 'mixed', 'onboarded': True,
            'accounts': [{'id': 'eur', 'name': 'EUR', 'currency': 'EUR', 'balance': 110000, 'confirmed_on': '2026-10-29'},
                         {'id': 'huf', 'name': 'HUF unknown', 'currency': 'HUF', 'balance': None, 'confirmed_on': None}],
            'incomes': [{'id': 'received', 'account_id': 'eur', 'amount': 10000, 'received_on': '2026-10-29', 'effect': 'add'}],
            'planning': {'active': True, 'account_id': 'eur', 'horizon': '2026-11-28', 'protected': 10000,
                'bills_confirmed': True, 'debts_confirmed': True, 'goal': {'name': 'Reserve', 'target': 100000, 'saved': 4000},
                'bills': [{'id': 'bill', 'label': 'Essentials', 'amount': 80000, 'currency': 'EUR', 'due': '2026-11-05', 'status': 'unpaid', 'source': 'manual'}],
                'steps': [{'id': 'step', 'account_id': 'eur', 'currency': 'EUR', 'amount': 4000, 'status': 'completed', 'created_on': '2026-10-29', 'completed_on': '2026-10-29'}], 'deferred': False}}
        receipt_command = {'kind': 'synthetic-receipt', 'amount': 4000}
        fingerprint = hashlib.sha256(json.dumps(receipt_command, sort_keys=True).encode()).hexdigest()
        with database(self.db) as connection:
            connection.executescript(ddl)
            for owner, state in [('legacy', old), ('expanded', current)]:
                # Noncanonical formatting/Unicode prove adoption never reserializes JSON.
                payload = json.dumps(state, ensure_ascii=False, indent=3)
                connection.execute('INSERT INTO demo_state VALUES (?,?,?)', (owner, 7, payload))
                connection.execute('INSERT INTO command_receipt VALUES (?,?,?,?)', (owner, 'receipt-1', fingerprint, ' {"revision": 7, "reserved": 4000} '))
                connection.execute('INSERT INTO import_preview VALUES (?,?,?)', (owner, 'preview-1', ' {"original": "opaque\u00e9", "amount": 2000} '))
                connection.execute('INSERT INTO coordination_run VALUES (?,?,?,?,?)', (owner, 'run-1', 7, 'published', '{ "version":7, "source":"synthetic" }'))
                connection.execute('INSERT INTO published_recommendation VALUES (?,?,?,?)', (owner, 'publication-1', 7, '{ "amount":4000, "source":"synthetic" }'))
        return receipt_command

    def test_empty_upgrade_downgrade_upgrade(self):
        self.migrate()
        self.assertEqual(set(self.raw()), set(TABLES))
        self.assertTrue(all(not rows for rows in self.raw().values()))
        with database(self.db) as connection:
            self.assertEqual(connection.execute('SELECT version_num FROM alembic_version').fetchall(), [('0001_initial_schema',)])
        self.migrate('downgrade', 'base')
        with database(self.db) as connection:
            self.assertEqual(connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'").fetchall(), [])
        self.migrate()
        self.assertTrue(all(not rows for rows in self.raw().values()))

    def test_legacy_and_expanded_rows_preserved_byte_for_byte_and_retry_restart(self):
        receipt_command = self.seed()
        before = self.raw()
        self.migrate()
        self.assertEqual(self.raw(), before)
        store = Store(self.url)
        try:
            self.assertEqual(store.read('legacy').snapshot.cash, 100000)
            self.assertEqual(store.read('expanded').personal.accounts[0].balance, 110000)
            self.assertIsNone(store.read('expanded').personal.accounts[1].balance)
            self.assertEqual(store.read('expanded').personal.planning.goal.saved, 4000)
            for owner in ('legacy', 'expanded'):
                replay = store.mutate(owner, 'receipt-1', 0, receipt_command,
                                     lambda s: self.fail('Receipt replay must not apply'), lambda s: self.fail('Receipt replay must not render'))
                self.assertEqual(replay, {'revision': 7, 'reserved': 4000})
                self.assertIn('opaque', store.get_preview(owner, 'preview-1'))
                self.assertEqual(json.loads(store.get_run(owner, 'run-1'))['version'], 7)
                self.assertEqual(json.loads(store.get_publication(owner, 'publication-1'))['amount'], 4000)
            self.assertEqual(self.raw(), before)
            store.mutate('expanded', 'new-command', 7, {'kind': 'synthetic-write'}, lambda s: setattr(s, 'deferred', True), lambda s: {'revision': s.revision})
        finally:
            store.engine.dispose()
        restarted = Store(self.url)
        try:
            self.assertEqual(restarted.read('expanded').revision, 8)
            self.assertTrue(restarted.read('expanded').deferred)
            self.assertEqual(restarted.mutate('expanded', 'new-command', 7, {'kind': 'synthetic-write'}, lambda s: self.fail('Double write'), lambda s: {}), {'revision': 8})
        finally:
            restarted.engine.dispose()

    def test_store_bootstrap_adopts_legacy_without_rewriting(self):
        self.seed()
        before = self.raw()
        store = Store(self.url)
        store.engine.dispose()
        self.assertEqual(self.raw(), before)
        self.migrate()
        self.assertEqual(self.raw(), before)

    def test_concurrent_store_bootstrap_preserves_legacy_rows(self):
        self.seed()
        before = self.raw()
        def start(_):
            store = Store(self.url)
            try:
                return store.read('legacy').snapshot.cash
            finally:
                store.engine.dispose()
        with ThreadPoolExecutor(max_workers=3) as pool:
            self.assertEqual(list(pool.map(start, range(3))), [100000]*3)
        self.assertEqual(self.raw(), before)

    def test_failed_initial_ddl_rolls_back_and_retry_succeeds(self):
        original = Operations.create_table
        def interrupted(operations, table_name, *args, **kwargs):
            result = original(operations, table_name, *args, **kwargs)
            if table_name == 'command_receipt':
                raise RuntimeError('Synthetic DDL interruption')
            return result
        with patch.object(Operations, 'create_table', interrupted):
            with self.assertRaisesRegex(RuntimeError, 'Synthetic DDL interruption'):
                self.migrate()
        self.assertEqual(self.schema(), [])
        self.migrate()
        self.assertTrue(all(not rows for rows in self.raw().values()))

    def test_populated_downgrade_refused_without_explicit_disposable_flag(self):
        self.seed()
        self.migrate()
        before, schema = self.raw(), self.schema()
        with self.assertRaisesRegex(RuntimeError, 'disposable'):
            self.migrate('downgrade', 'base')
        self.assertEqual(self.raw(), before)
        self.assertEqual(self.schema(), schema)
        # This database is a freshly created disposable fixture, explicitly flagged.
        self.migrate('downgrade', 'base', disposable=True)
        self.migrate()
        self.assertTrue(all(not rows for rows in self.raw().values()))

    def test_unknown_or_mismatched_schema_fails_before_changes(self):
        changes = ('CREATE TABLE unexpected (id INTEGER)', 'ALTER TABLE demo_state ADD COLUMN surprise TEXT',
                   'CREATE INDEX unexpected_index ON demo_state(revision)', 'DROP TABLE import_preview')
        for change in changes:
            with self.subTest(change=change):
                if self.db.exists():
                    self.db.unlink()
                self.seed()
                with database(self.db) as connection:
                    connection.execute(change)
                before = self.schema()
                with self.assertRaisesRegex(RuntimeError, 'schema'):
                    self.migrate()
                self.assertEqual(self.schema(), before)

    def test_unknown_revision_fails_before_changes(self):
        self.migrate()
        with database(self.db) as connection:
            connection.execute("UPDATE alembic_version SET version_num='unrecognized_future_version'")
        before = self.schema()
        with self.assertRaises(Exception):
            self.migrate()
        self.assertEqual(self.schema(), before)
        with database(self.db) as connection:
            self.assertEqual(connection.execute('SELECT version_num FROM alembic_version').fetchone()[0], 'unrecognized_future_version')

    def test_mismatched_type_nullable_key_and_trigger_fail_closed(self):
        variants = (
            LEGACY_DDL.replace('revision INTEGER NOT NULL', 'revision TEXT NOT NULL', 1),
            LEGACY_DDL.replace('revision INTEGER NOT NULL', 'revision INTEGER', 1),
            LEGACY_DDL.replace('PRIMARY KEY(owner,key)', 'PRIMARY KEY(key,owner)', 1),
            LEGACY_DDL + "CREATE TRIGGER unexpected_trigger AFTER INSERT ON demo_state BEGIN SELECT 1; END;",
        )
        for ddl in variants:
            with self.subTest(ddl=ddl):
                if self.db.exists():
                    self.db.unlink()
                self.seed(ddl)
                rows, schema = self.raw(), self.schema()
                with self.assertRaisesRegex(RuntimeError, 'schema'):
                    Store(self.url)
                self.assertEqual(self.raw(), rows)
                self.assertEqual(self.schema(), schema)

    def test_cli_requires_explicit_url_and_operates_on_disposable_database(self):
        args = [sys.executable, '-m', 'alembic', '-c', str(API/'alembic.ini')]
        missing = subprocess.run([*args, 'upgrade', 'head'], capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn('explicit -x database_url', missing.stderr)
        self.assertFalse(self.db.exists())
        for verb, target in [('upgrade', 'head'), ('downgrade', 'base'), ('upgrade', 'head')]:
            result = subprocess.run([*args, '-x', 'database_url='+self.url, verb, target], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(not rows for rows in self.raw().values()))
