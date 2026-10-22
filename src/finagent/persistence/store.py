"""SQLite unit-of-work. JSON snapshots retain domain independence."""

import json
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import event
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Record(SQLModel, table=True):
    key: str = Field(primary_key=True)
    payload: str


class HistoryEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    timestamp: str
    type: str
    payload: str


class Store:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(self.engine, "connect")
        def configure(dbapi_connection: Any, connection_record: Any) -> None:
            dbapi_connection.execute("PRAGMA busy_timeout=5000")

        SQLModel.metadata.create_all(self.engine)

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        with Session(self.engine) as session:
            # Serialize writers across processes: daily issuance and ledger updates are atomic.
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise


def get(session: Session, key: str, default: Any = None) -> Any:
    row = session.get(Record, key)
    return json.loads(row.payload) if row else default


def put(session: Session, key: str, value: Any) -> None:
    row = session.get(Record, key)
    if row:
        row.payload = json.dumps(value)
    else:
        row = Record(key=key, payload=json.dumps(value))
    session.add(row)
    session.flush()


def log(session: Session, timestamp: str, kind: str, payload: Any) -> None:
    session.add(HistoryEvent(timestamp=timestamp, type=kind, payload=json.dumps(payload)))
    session.flush()


def history(session: Session, kind: str | None = None) -> list[dict[str, Any]]:
    query = select(HistoryEvent).order_by(HistoryEvent.id.desc())
    if kind:
        query = query.where(HistoryEvent.type == kind)
    return [
        {"id": x.id, "timestamp": x.timestamp, "type": x.type, "payload": json.loads(x.payload)}
        for x in session.exec(query).all()
    ]
