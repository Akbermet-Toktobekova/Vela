"""Local-only bank CSV parsing with explicit row-level diagnostics."""

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from finagent.domain.models import Money, Transaction

DEFAULT_KEYWORDS = {
    "spotify": "subscriptions",
    "netflix": "subscriptions",
    "rent": "housing",
    "market": "groceries",
    "tesco": "groceries",
    "takeout": "dining",
    "restaurant": "dining",
    "salary": "income",
}


def parse_amount(raw: str) -> int:
    value = re.sub(r"[\s\u00a0$€£]", "", raw.strip())
    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]
    if "," in value and "." in value:
        value = (
            value.replace(",", "")
            if value.rfind(".") > value.rfind(",")
            else value.replace(".", "").replace(",", ".")
        )
    elif "," in value:
        value = value.replace(",", ".")
    number = Decimal(value)
    if not number.is_finite():
        raise ValueError("Non-finite amount")
    return Money(100).scale(number).cents


def parse_date(raw: str, fmt: str | None = None) -> str:
    formats = (
        [fmt] if fmt else ["%Y-%m-%d", "%Y.%m.%d", "%Y.%m.%d.", "%d/%m/%Y", "%d.%m.%Y", "%m/%d/%Y"]
    )
    for item in formats:
        try:
            return datetime.strptime(raw.strip(), item).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Unrecognized date; provide date_format")


@dataclass
class ImportResult:
    transactions: list[Transaction]
    errors: list[dict[str, Any]]
    detected: dict[str, Any]


def parse_csv(
    content: bytes,
    user_id: str,
    mapping: dict[str, str] | None = None,
    keywords: dict[str, str] | None = None,
) -> ImportResult:
    if mapping is not None and (
        not isinstance(mapping, dict)
        or not all(isinstance(k, str) and isinstance(v, str) for k, v in mapping.items())
    ):
        raise ValueError("Column mapping must be an object of strings")
    if keywords is not None and (
        not isinstance(keywords, dict)
        or not all(isinstance(k, str) and isinstance(v, str) for k, v in keywords.items())
    ):
        raise ValueError("Category keywords must be an object of strings")
    mapping = mapping or {}
    keywords = keywords or DEFAULT_KEYWORDS
    encoding = "utf-8-sig"
    try:
        text = content.decode(encoding)
    except UnicodeDecodeError:
        encoding = "cp1250"
        text = content.decode(encoding)
    if not text.strip():
        raise ValueError("The statement is empty")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error as exc:
        raise ValueError("Cannot detect columns; use a delimited CSV") from exc
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = {h.lower().strip(): h for h in reader.fieldnames or []}
    aliases = {
        "date": ["date", "datum", "dátum", "booking date"],
        "amount": ["amount", "összeg", "signed amount"],
        "description": ["description", "leírás", "merchant", "details"],
        "debit": ["debit", "withdrawal"],
        "credit": ["credit", "deposit"],
    }
    columns = {
        key: mapping.get(key) or next((headers[a] for a in names if a in headers), "")
        for key, names in aliases.items()
    }
    if not columns["date"] or not (columns["amount"] or columns["debit"] or columns["credit"]):
        raise ValueError("Map a date and an amount (or debit/credit) column")
    rows, errors = [], []
    digest = hashlib.sha256(content).hexdigest()[:16]
    for line, row in enumerate(reader, 2):
        try:
            when = parse_date(row.get(columns["date"], ""), mapping.get("date_format"))
            amount = (
                parse_amount(row.get(columns["amount"], ""))
                if columns["amount"]
                else parse_amount(row.get(columns["credit"], "") or "0")
                - abs(parse_amount(row.get(columns["debit"], "") or "0"))
            )
            desc = row.get(columns["description"], "") or "Imported transaction"
            category = next(
                (value for key, value in keywords.items() if key.casefold() in desc.casefold()),
                "income" if amount > 0 else "other",
            )
            rows.append(
                Transaction(
                    f"csv-{digest}-{line}", user_id, when, amount, desc, desc, category, "csv"
                )
            )
        except (ValueError, InvalidOperation, TypeError) as exc:
            errors.append({"line": line, "message": str(exc) or "Malformed row"})
    return ImportResult(
        rows,
        errors,
        {
            "encoding": encoding,
            "delimiter": dialect.delimiter,
            "columns": columns,
            "date_policy": "day-first when ambiguous; override date_format if needed",
        },
    )


class CsvStatementSource:
    def __init__(self, result: ImportResult) -> None:
        self.result = result

    def fetch(self, user_id: str, since: date) -> Iterable[Transaction]:
        return [
            t
            for t in self.result.transactions
            if t.user_id == user_id and t.date >= since.isoformat()
        ]
