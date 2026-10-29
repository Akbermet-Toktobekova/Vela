"""Transactional local store; intentionally limited to one synthetic demo identity."""
import hashlib
import json
from pathlib import Path
from threading import RLock
from alembic import command
from alembic.config import Config
from sqlalchemy import Column, Integer, MetaData, String, Table, Text, UniqueConstraint, create_engine, select, update, delete
from .domain import State


class Conflict(Exception):
    pass


metadata = MetaData()
states = Table("demo_state", metadata, Column("owner", String, primary_key=True),
               Column("revision", Integer, nullable=False), Column("payload", Text, nullable=False))
receipts = Table("command_receipt", metadata, Column("owner", String, primary_key=True),
                 Column("key", String, primary_key=True), Column("fingerprint", String, nullable=False),
                 Column("response", Text, nullable=False))
# Parsed-but-not-applied statement imports. Kept outside State so previews never bump the revision.
previews = Table("import_preview", metadata, Column("owner", String, primary_key=True),
                 Column("id", String, primary_key=True), Column("payload", Text, nullable=False))
# Durable coordination runs and published recommendation cards (§10).
coordination_runs = Table("coordination_run", metadata, Column("owner", String, primary_key=True),
                          Column("run_id", String, primary_key=True), Column("financial_revision", Integer, nullable=False),
                          Column("status", String, nullable=False), Column("payload", Text, nullable=False))
published_recommendations = Table("published_recommendation", metadata, Column("owner", String, primary_key=True),
                                  Column("publication_key", String, primary_key=True),
                                  Column("financial_revision", Integer, nullable=False),
                                  Column("payload", Text, nullable=False))

# Alembic's command environment uses module-level proxies; serialize bootstrap
# inside a process, while SQLite BEGIN IMMEDIATE coordinates separate starters.
_migration_lock = RLock()

private_originals = Table('private_original', metadata,
    Column('owner', String, primary_key=True), Column('file_id', String, primary_key=True),
    Column('backend', String, nullable=False), Column('object_key', String, nullable=False),
    Column('sha256', String, nullable=False), Column('size', Integer, nullable=False),
    Column('created_at', Integer, nullable=False), Column('expires_at', Integer, nullable=False),
    Column('status', String, nullable=False))

import_generations = Table('import_generation', metadata, Column('owner', String, primary_key=True), Column('generation', String, nullable=False))
import_jobs = Table('import_job', metadata,
    Column('owner', String, primary_key=True), Column('job_id', String, primary_key=True),
    Column('key', String, nullable=False), Column('fingerprint', String, nullable=False),
    Column('generation', String, nullable=False), Column('file_id', String, nullable=False),
    Column('version', Integer, nullable=False), Column('status', String, nullable=False),
    Column('attempts', Integer, nullable=False), Column('next_attempt_at', Integer, nullable=False),
    Column('lease_until', Integer, nullable=False), Column('lease_token', String, nullable=False),
    Column('created_at', Integer, nullable=False), Column('updated_at', Integer, nullable=False),
    Column('payload', Text, nullable=False), UniqueConstraint('owner', 'key', name='uq_import_job_owner_key'))


class Store:
    def __init__(self, url: str):
        self.engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
        config = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
        try:
            with _migration_lock, self.engine.begin() as connection:
                if connection.dialect.name == 'sqlite':
                    connection.exec_driver_sql('BEGIN IMMEDIATE')
                config.attributes['connection'] = connection
                command.upgrade(config, 'head')
        except Exception:
            self.engine.dispose()
            raise
        self.lock = RLock()

    def read(self, owner: str) -> State:
        with self.engine.connect() as conn:
            row = conn.execute(select(states.c.payload).where(states.c.owner == owner)).first()
            return State.model_validate_json(row[0]) if row else State()

    def mutate(self, owner: str, key: str, revision: int, command: dict, apply, render) -> dict:
        fingerprint = hashlib.sha256(json.dumps(command, sort_keys=True).encode()).hexdigest()
        with self.lock, self.engine.begin() as conn:
            old = conn.execute(select(receipts).where(receipts.c.owner == owner, receipts.c.key == key)).mappings().first()
            if old:
                if old["fingerprint"] != fingerprint:
                    raise Conflict("This retry key was used with different data.")
                return json.loads(old["response"])
            row = conn.execute(select(states).where(states.c.owner == owner)).mappings().first()
            state = State.model_validate_json(row["payload"]) if row else State()
            if state.revision != revision:
                raise Conflict("Your information changed. Refresh and try again.")
            apply(state)
            state.revision += 1
            state.history.append({"event": command["kind"], "revision": state.revision})
            if row:
                result = conn.execute(update(states).where(states.c.owner == owner, states.c.revision == revision)
                                      .values(revision=state.revision, payload=state.model_dump_json()))
                if result.rowcount != 1:
                    raise Conflict("Your information changed. Refresh and try again.")
            else:
                conn.execute(states.insert().values(owner=owner, revision=state.revision, payload=state.model_dump_json()))
            response = render(state)
            conn.execute(receipts.insert().values(owner=owner, key=key, fingerprint=fingerprint, response=json.dumps(response)))
            return response

    def erase(self, owner: str):
        with self.lock, self.engine.begin() as conn:
            conn.execute(delete(import_jobs).where(import_jobs.c.owner == owner))
            conn.execute(delete(import_generations).where(import_generations.c.owner == owner))
            conn.execute(delete(receipts).where(receipts.c.owner == owner))
            conn.execute(delete(states).where(states.c.owner == owner))
            conn.execute(delete(previews).where(previews.c.owner == owner))
            conn.execute(delete(coordination_runs).where(coordination_runs.c.owner == owner))
            conn.execute(delete(published_recommendations).where(published_recommendations.c.owner == owner))

    def save_run(self, owner: str, run_id: str, financial_revision: int, status: str, payload: str):
        with self.lock, self.engine.begin() as conn:
            existing = conn.execute(
                select(coordination_runs.c.run_id).where(
                    coordination_runs.c.owner == owner,
                    coordination_runs.c.run_id == run_id,
                )
            ).first()
            if existing:
                conn.execute(
                    update(coordination_runs)
                    .where(coordination_runs.c.owner == owner, coordination_runs.c.run_id == run_id)
                    .values(financial_revision=financial_revision, status=status, payload=payload)
                )
            else:
                conn.execute(
                    coordination_runs.insert().values(
                        owner=owner,
                        run_id=run_id,
                        financial_revision=financial_revision,
                        status=status,
                        payload=payload,
                    )
                )

    def get_run(self, owner: str, run_id: str) -> str | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                select(coordination_runs.c.payload).where(
                    coordination_runs.c.owner == owner,
                    coordination_runs.c.run_id == run_id,
                )
            ).first()
            return row[0] if row else None

    def get_publication(self, owner: str, publication_key: str) -> str | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                select(published_recommendations.c.payload).where(
                    published_recommendations.c.owner == owner,
                    published_recommendations.c.publication_key == publication_key,
                )
            ).first()
            return row[0] if row else None

    def get_latest_publication(self, owner: str) -> str | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                select(published_recommendations.c.payload)
                .where(published_recommendations.c.owner == owner)
                .order_by(published_recommendations.c.financial_revision.desc())
            ).first()
            return row[0] if row else None

    def publish_atomic(
        self,
        owner: str,
        run_id: str,
        publication_key: str,
        expected_revision: int,
        run_payload_fn,
        publication_payload: str,
    ) -> dict:
        """Atomically validates that the store's current financial revision still matches
        `expected_revision`, deduplicates by `publication_key`, persists the published card,
        and marks the coordination run as `published`. Raises `Conflict` if state revision
        has changed (e.g. newer income or bill arrived during processing).
        """
        with self.lock, self.engine.begin() as conn:
            existing_pub = conn.execute(
                select(published_recommendations.c.payload).where(
                    published_recommendations.c.owner == owner,
                    published_recommendations.c.publication_key == publication_key,
                )
            ).first()
            if existing_pub:
                return json.loads(existing_pub[0])

            row = conn.execute(select(states.c.revision).where(states.c.owner == owner)).first()
            current_revision = row[0] if row else 0
            if current_revision != expected_revision:
                raise Conflict(
                    f"Stale coordination run: expected revision {expected_revision}, current is {current_revision}."
                )

            conn.execute(
                published_recommendations.insert().values(
                    owner=owner,
                    publication_key=publication_key,
                    financial_revision=expected_revision,
                    payload=publication_payload,
                )
            )
            final_run_payload = run_payload_fn()
            conn.execute(
                update(coordination_runs)
                .where(coordination_runs.c.owner == owner, coordination_runs.c.run_id == run_id)
                .values(status="published", payload=final_run_payload)
            )
            return json.loads(publication_payload)

    def save_preview(self, owner: str, preview_id: str, payload: str, keep: int = 5):
        with self.lock, self.engine.begin() as conn:
            conn.execute(previews.insert().values(owner=owner, id=preview_id, payload=payload))
            ids = [r[0] for r in conn.execute(select(previews.c.id).where(previews.c.owner == owner).order_by(previews.c.id.desc()))]
            if len(ids) > keep:
                conn.execute(delete(previews).where(previews.c.owner == owner, previews.c.id.in_(ids[keep:])))

    def get_preview(self, owner: str, preview_id: str) -> str | None:
        with self.engine.connect() as conn:
            row = conn.execute(select(previews.c.payload).where(previews.c.owner == owner, previews.c.id == preview_id)).first()
            return row[0] if row else None

    def delete_preview(self, owner: str, preview_id: str, conn=None):
        with self.lock, self.engine.begin() as c:
            c.execute(delete(previews).where(previews.c.owner == owner, previews.c.id == preview_id))

    def add_original(self, owner, file_id, **values):
        with self.lock, self.engine.begin() as conn:
            conn.execute(private_originals.insert().values(owner=owner, file_id=file_id, **values))

    def get_original(self, owner, file_id):
        with self.engine.connect() as conn:
            row = conn.execute(select(private_originals).where(private_originals.c.owner == owner, private_originals.c.file_id == file_id)).mappings().first()
            return dict(row) if row else None

    def list_originals(self, owner=None):
        statement = select(private_originals)
        if owner is not None:
            statement = statement.where(private_originals.c.owner == owner)
        with self.engine.connect() as conn:
            return [dict(row) for row in conn.execute(statement).mappings()]

    def original_status(self, owner, file_id, status):
        if status not in ('ready', 'delete_pending'):
            raise ValueError('Invalid original lifecycle transition.')
        with self.lock, self.engine.begin() as conn:
            conn.execute(update(private_originals).where(private_originals.c.owner == owner, private_originals.c.file_id == file_id).values(status=status))

    def activate_original(self, owner, file_id):
        with self.lock, self.engine.begin() as conn:
            result = conn.execute(update(private_originals).where(private_originals.c.owner == owner,
                private_originals.c.file_id == file_id, private_originals.c.status == 'pending').values(status='ready'))
            return result.rowcount == 1

    def original_cleanup_intent(self, owner, file_id, **values):
        with self.lock, self.engine.begin() as conn:
            row = conn.execute(select(private_originals.c.file_id).where(private_originals.c.owner == owner, private_originals.c.file_id == file_id)).first()
            if row is None:
                conn.execute(private_originals.insert().values(owner=owner, file_id=file_id, status='delete_pending', **values))
            else:
                conn.execute(update(private_originals).where(private_originals.c.owner == owner, private_originals.c.file_id == file_id).values(status='delete_pending'))

    def remove_original(self, owner, file_id):
        with self.lock, self.engine.begin() as conn:
            conn.execute(delete(private_originals).where(private_originals.c.owner == owner, private_originals.c.file_id == file_id))
