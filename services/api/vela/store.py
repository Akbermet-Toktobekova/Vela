"""Transactional local store; intentionally limited to one synthetic demo identity."""
import hashlib
import json
from threading import RLock
from sqlalchemy import Column, Integer, MetaData, String, Table, Text, create_engine, select, update, delete
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


class Store:
    def __init__(self, url: str):
        self.engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
        metadata.create_all(self.engine)
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
            conn.execute(delete(receipts).where(receipts.c.owner == owner))
            conn.execute(delete(states).where(states.c.owner == owner))
            conn.execute(delete(previews).where(previews.c.owner == owner))

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
