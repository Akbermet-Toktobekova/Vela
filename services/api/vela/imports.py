"""Statement import: local CSV/XLSX/PDF parsing, Gemini for PDFs/images and unrecognised layouts."""
import csv
import hashlib
import io
import os
import re
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Literal
from pydantic import BaseModel, Field
from .ai import Quotas, generate, estimate_tokens, AIUnavailable, enabled, parse_json
from .domain import CATEGORIES, Category, Record, Transaction, SignedMoney
from .pii import is_pii_masking_enabled, mask_pii
from .reconciliation import SourceRow

MAX_BYTES = 15 * 1024 * 1024
MAX_ROWS = 3000


class Recurring(Record):
    id: str
    label: str
    amount: int
    next_due: date
    occurrences: int
    kind: Literal["living", "rent", "debt", "other"]


class ImportPreview(Record):
    id: str
    filename: str
    file_type: Literal["csv", "xlsx", "pdf", "image"]
    parser: Literal["local", "gemini"]
    model: str | None = None
    currency: str = "EUR"
    period_start: date | None = None
    period_end: date | None = None
    opening_balance: SignedMoney | None = None
    closing_balance: SignedMoney | None = None
    income: int = 0
    spending: int = 0
    refunds: int = 0
    net_spending: int = 0
    transactions: list[Transaction] = Field(default_factory=list)
    recurring: list[Recurring] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_checksum: str | None = None
    source_method_version: str = 'parsed-source-v1'
    source_rows: list[SourceRow] = Field(default_factory=list)


class ImportError_(ValueError):
    pass


def raw_document_ai_allowed() -> bool:
    """Raw documents require explicit consent while PII masking is enabled."""
    return not is_pii_masking_enabled() or os.getenv("ALLOW_RAW_DOCUMENT_AI", "").strip().lower() == "true"


# ---------- value parsing ----------

DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d",
                "%d/%m/%y", "%m/%d/%y", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%Y%m%d", "%d-%b-%Y", "%d-%b-%y")


def _date_token(value: str) -> str:
    value = value.strip().strip('"').strip("'")
    if "T" in value[:11] and value[:4].isdigit():
        value = value.split("T")[0]
    if re.match(r"^\d{4}-\d{2}-\d{2} \d", value) or re.match(r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4} \d", value):
        value = value.split(" ")[0]
    return value


def parse_date(value: str, fmt: str) -> date | None:
    try:
        return datetime.strptime(_date_token(value), fmt).date()
    except (ValueError, TypeError):
        return None


def parse_any_date(value: str) -> date | None:
    token = _date_token(value)
    if not token:
        return None
    for fmt in DATE_FORMATS:
        d = parse_date(token, fmt)
        if d and 1990 <= d.year <= 2100:
            return d
    return None


def pick_date_format(values: list[str]) -> str | None:
    sample = [v for v in values if v and v.strip()][:200]
    if not sample:
        return None
    best, best_count = None, 0
    for fmt in DATE_FORMATS:
        count = sum(1 for v in sample if parse_date(v, fmt))
        if count > best_count:
            best, best_count = fmt, count
    return best if best_count >= max(1, len(sample) * 0.4) else None


def comma_decimal(values: list[str]) -> bool:
    comma = sum(1 for v in values if re.search(r",\d{1,2}\s*[a-zA-Z€$£₽]*\s*-?\)?\s*$", v.strip()))
    dot = sum(1 for v in values if re.search(r"\.\d{1,2}\s*[a-zA-Z€$£₽]*\s*-?\)?\s*$", v.strip()))
    return comma > dot


def parse_amount(value, decimal_comma: bool) -> int | None:
    """Returns signed cents. Accepts 1.234,56 / 1,234.56 / (12.30) / 12.30- / €12 / 12 EUR / DR / CR."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int((Decimal(str(value)) * 100).quantize(Decimal("1")))
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}", text) or re.fullmatch(r"\d{4}[./-]\d{1,2}[./-]\d{1,2}", text):
        return None
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative, text = True, text[1:-1]
    if re.search(r"(?i)\b(dr|debit|soll|d)\s*$", text):
        negative = True
        text = re.sub(r"(?i)\b(dr|debit|soll|d)\s*$", "", text)
    elif re.search(r"(?i)\b(cr|credit|haben|h)\s*$", text):
        text = re.sub(r"(?i)\b(cr|credit|haben|h)\s*$", "", text)
    text = text.replace("\u00a0", "").replace("\u202f", "").replace(" ", "").replace("'", "")
    text = re.sub(r"(?i)(eur|€|usd|\$|gbp|£|chf|pln|zł|rub|₽|kzt|₸|uzs|try|₺)", "", text)
    if text.endswith("-") or text.endswith("−"):
        negative, text = True, text[:-1]
    if text.startswith("+"):
        text = text[1:]
    if text.startswith("-") or text.startswith("−"):
        negative, text = not negative, text[1:]
    if not re.fullmatch(r"[\d.,]+", text):
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        if decimal_comma or re.search(r",\d{1,2}$", text):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "." in text and decimal_comma and not re.search(r"\.\d{1,2}$", text):
        text = text.replace(".", "")
    try:
        cents = int((Decimal(text) * 100).quantize(Decimal("1")))
    except InvalidOperation:
        return None
    return -cents if negative else cents


# ---------- column detection ----------

KEYS = {
    "date": ["booking date", "buchungstag", "buchungsdatum", "transaction date", "posting date", "date", "datum",
             "completed date", "started date", "fecha", "data", "дата", "date opération", "valuta", "value date",
             "wertstellung", "operazione", "transaktionsdatum", "tarikh", "sana"],
    "amount": ["amount", "betrag", "importe", "montant", "сумма", "bedrag", "importo", "kwota", "umsatz", "value",
               "summe", "net amount", "total", "tutar", "miqdor", "summa"],
    "debit": ["debit", "withdrawal", "soll", "ausgang", "paid out", "money out", "lastschrift", "cargo", "débit",
              "outflow", " списание", "расход", "chiqim"],
    "credit": ["credit", "deposit", "haben", "eingang", "paid in", "money in", "gutschrift", "abono", "crédit",
               "inflow", "пополнение", "приход", "kirim"],
    "description": ["description", "verwendungszweck", "beschreibung", "details", "payee", "merchant", "buchungstext",
                    "memo", "reference", "concepto", "libellé", "counterparty", "empfänger", "auftraggeber",
                    "begünstigter", "beguenstigter", "narrative", "name", "text", "zahlungsempfänger", "partner",
                    "назначение", "описание", "получатель", "контрагент", "note", "title", "category", "type", "izoh"],
    "balance": ["balance", "saldo", "kontostand", "solde", "остаток", "баланс", "running balance", "qoldiq"],
}


def _match(header: str, words: list[str]) -> int | None:
    h = header.strip().lower()
    for rank, w in enumerate(words):
        w = w.strip()
        if h == w or h.startswith(w) or f" {w}" in f" {h}":
            return rank
    return None


def map_columns(header: list[str]) -> dict:
    mapping: dict = {"description": []}
    for field in ("date", "amount", "debit", "credit", "balance"):
        best = None
        for i, h in enumerate(header):
            if field != "date" and _match(h, KEYS["date"]) is not None:
                continue  # "Value date" is a date column, not an amount
            rank = _match(h, KEYS[field])
            if rank is not None and (best is None or rank < best[0]):
                best = (rank, i)
        if best:
            mapping[field] = best[1]
    used = {mapping.get(k) for k in ("date", "amount", "debit", "credit", "balance")}
    for i, h in enumerate(header):
        if i not in used and _match(h, KEYS["description"]) is not None:
            mapping["description"].append(i)
    return mapping


def find_header(rows: list[list[str]]) -> int | None:
    for i, row in enumerate(rows[:60]):
        m = map_columns(row)
        if "date" in m and ("amount" in m or "debit" in m or "credit" in m):
            return i
    return None


def infer_columns(rows: list[list[str]]) -> tuple[int, dict] | None:
    """Fallback when headers are missing or in an unknown language: inspect cell values."""
    best_start = None
    for idx, row in enumerate(rows[:60]):
        if len(row) < 2:
            continue
        has_date = any(parse_any_date(c) is not None for c in row)
        has_amt = any(parse_amount(c, True) is not None or parse_amount(c, False) is not None for c in row)
        if has_date and has_amt:
            best_start = idx
            break
    if best_start is None:
        return None
    sample = rows[best_start:best_start + 50]
    width = max(len(r) for r in sample)
    date_col = max(range(width), key=lambda c: sum(1 for r in sample if c < len(r) and parse_any_date(r[c]) is not None))
    amt_scores = []
    for c in range(width):
        if c == date_col:
            continue
        score = sum(1 for r in sample if c < len(r) and parse_any_date(r[c]) is None and (parse_amount(r[c], True) is not None or parse_amount(r[c], False) is not None))
        amt_scores.append((score, c))
    amt_scores.sort(reverse=True)
    if not amt_scores or amt_scores[0][0] == 0:
        return None
    amount_col = amt_scores[0][1]
    desc_cols = [c for c in range(width) if c not in (date_col, amount_col)]
    return best_start, {"date": date_col, "amount": amount_col, "description": desc_cols}


def decode(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    for enc in ("utf-8-sig", "cp1252", "cp1251", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def csv_rows(text: str) -> list[list[str]]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    sample = "\n".join(lines[:50])
    counts = {d: sample.count(d) for d in (";", ",", "\t", "|")}
    delimiter = max(counts, key=counts.get) if any(counts.values()) else ","
    return [row for row in csv.reader(io.StringIO(text), delimiter=delimiter) if any(c.strip() for c in row)]


def xlsx_rows(data: bytes) -> list[list[str]]:
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    rows = []
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            cells = []
            for c in row:
                if c is None:
                    cells.append("")
                elif isinstance(c, datetime):
                    cells.append(c.date().isoformat())
                elif isinstance(c, date):
                    cells.append(c.isoformat())
                elif isinstance(c, float):
                    cells.append(f"{c:.2f}")
                else:
                    cells.append(str(c))
            if any(x.strip() for x in cells):
                rows.append(cells)
            if len(rows) > MAX_ROWS + 60:
                break
        if rows:
            break
    return rows


def pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages[:60]).strip()
    except Exception:
        return ""


def parse_pdf_lines(text: str) -> list[dict]:
    """Regex fallback for text-based PDFs when Gemini is offline or rate-limited."""
    out = []
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s+(.+?)\s+([+\-−]?\s*(?:€|EUR)?\s*\d[\d.,]*[.,]\d{2}\s*(?:€|EUR|[+\-−])?)\s*$", re.IGNORECASE)
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        m = pattern.match(line)
        if not m:
            continue
        d = parse_any_date(m.group(1))
        amt_str = m.group(3)
        dec_comma = "," in amt_str and ("." not in amt_str or amt_str.rfind(",") > amt_str.rfind("."))
        amt = parse_amount(amt_str, dec_comma)
        if d and amt:
            desc = m.group(2).strip()[:200] or "Transaction"
            out.append({"date": d, "description": desc, "amount": amt, "balance": None})
    return out


def tabular(rows: list[list[str]], source: str) -> tuple[list[dict], list[str], int | None]:
    """Returns parsed rows [{date, description, amount, balance}], warnings, closing balance."""
    head = find_header(rows)
    if head is not None:
        header, body = rows[head], rows[head+1:][:MAX_ROWS]
        m = map_columns(header)
        if not m["description"]:
            used = {m.get(k) for k in ("date", "amount", "debit", "credit", "balance")}
            m["description"] = [i for i in range(len(header)) if i not in used]
    else:
        inferred = infer_columns(rows)
        if inferred is None:
            raise ImportError_("Couldn't find date and amount columns.")
        start, m = inferred
        body = rows[start:][:MAX_ROWS]

    cell = lambda r, i: r[i] if i is not None and i < len(r) else ""
    fmt = pick_date_format([cell(r, m["date"]) for r in body])
    money_cols = [m.get(k) for k in ("amount", "debit", "credit", "balance") if m.get(k) is not None]
    dec_comma = comma_decimal([cell(r, i) for r in body for i in money_cols])
    out, skipped = [], 0
    for r in body:
        raw_date = cell(r, m["date"])
        d = (parse_date(raw_date, fmt) if fmt else None) or parse_any_date(raw_date)
        if "amount" in m:
            amount = parse_amount(cell(r, m["amount"]), dec_comma)
        else:
            debit = parse_amount(cell(r, m.get("debit")), dec_comma) or 0
            credit = parse_amount(cell(r, m.get("credit")), dec_comma) or 0
            amount = (abs(credit) - abs(debit)) if (debit or credit) else None
        if d is None or amount is None or amount == 0:
            skipped += 1
            continue
        desc = " · ".join(x.strip() for x in (cell(r, i) for i in m["description"]) if x.strip())
        desc = re.sub(r"\s+", " ", desc)[:200] or "Transaction"
        bal = parse_amount(cell(r, m.get("balance")), dec_comma) if "balance" in m else None
        headers = [str(h).strip().lower() for h in rows[head]] if head is not None else []
        def extra(names):
            index = next((i for i,h in enumerate(headers) if h in names), None)
            value = cell(r,index).strip() if index is not None else ''
            return value or None
        out.append({"date": d, "description": desc, "amount": amount, "balance": bal,
                    "bank_reference": extra(('reference','transaction id','transaction_id','bank reference')),
                    "booking_status": extra(('booking status','booking_status','status'))})
    warnings = [f"Skipped {skipped} row(s) without a readable date or amount."] if skipped else []
    if not out:
        raise ImportError_("No transactions found in this file.")
    closing = None
    with_bal = [x for x in out if x["balance"] is not None]
    if with_bal:
        latest = max(x["date"] for x in with_bal)
        same_day = [x for x in with_bal if x["date"] == latest]
        first_is_newest = out[0]["date"] >= out[-1]["date"]
        closing = same_day[0]["balance"] if first_is_newest else same_day[-1]["balance"]
    return out, warnings, closing


# ---------- categories and recurring bills ----------

KEYWORDS = {
    "income": ["salary", "gehalt", "lohn", "payroll", "nómina", "salaire", "zarplata", "зарплата", "стипендия", "доход"],
    "housing": ["rent", "miete", "alquiler", "loyer", "landlord", "hausverwaltung", "wohnung", "аренда", "квартира", "жкх"],
    "utilities": ["electric", "strom", "gas", "water", "wasser", "internet", "telekom", "vodafone", "o2 ", "energie", "stadtwerke", "phone", "mobile", "связь", "интернет"],
    "groceries": ["rewe", "edeka", "aldi", "lidl", "kaufland", "carrefour", "mercadona", "tesco", "spar", "billa", "netto", "penny", "supermarket", "dm-drogerie", "rossmann", "albert heijn", "jumbo", "продукты", "супермаркет", "корзинка", "магнит", "пятерочка"],
    "dining": ["restaurant", "cafe", "café", "coffee", "starbucks", "mcdonald", "burger", "pizza", "lieferando", "wolt", "uber eats", "deliveroo", "glovo", "bar ", "кафе", "ресторан", "яндекс еда"],
    "transport": ["uber", "bolt", "yandex go", "яндекс такси", "db ", "deutsche bahn", "bvg", "mvv", "tankstelle", "shell", "aral", "esso", "total", "fuel", "parking", "ryanair", "lufthansa", "flixbus", "train", "metro", "такси", "метро", "бензин"],
    "shopping": ["amazon", "zalando", "ikea", "h&m", "zara", "mediamarkt", "saturn", "ebay", "aliexpress", "otto", "wildberries", "ozon", "uzum"],
    "subscriptions": ["netflix", "spotify", "apple.com", "google", "youtube", "disney", "prime", "icloud", "adobe", "chatgpt", "openai", "gym", "fitness", "подписка"],
    "health": ["apotheke", "pharmacy", "farmacia", "doctor", "arzt", "clinic", "krankenkasse", "insurance", "versicherung", "аптека", "клиника"],
    "debt": ["loan", "kredit", "credit card", "kreditkarte", "darlehen", "klarna", "paypal ratenzahlung", "installment", "кредит", "рассрочка"],
    "transfers": ["transfer", "überweisung", "umbuchung", "savings", "sparen", "revolut", "wise", "перевод"],
    "cash": ["atm", "geldautomat", "cash withdrawal", "bargeld", "cajero", "банкомат", "снятие"],
    "fees": ["fee", "gebühr", "entgelt", "kontoführung", "commission", "interest charge", "комиссия"],
}


def keyword_category(description: str, amount: int) -> str:
    d = description.lower()
    if amount > 0 and re.search(r"\b(refund|refunded|erstattung|rückerstattung|возврат)\b", d):
        return "refunds"
    for cat, words in KEYWORDS.items():
        if any(w in d for w in words):
            if cat == "income" and amount < 0:
                continue
            return cat
    return "income" if amount > 0 else "other"


class _Cat(BaseModel):
    i: int
    category: Category


class _CatList(BaseModel):
    items: list[_Cat]


async def ai_categorize(txns: list[dict], quotas: Quotas) -> tuple[bool, str | None]:
    uniques: dict[str, int] = {}
    for t in txns:
        key = t["description"][:80]
        if key not in uniques and len(uniques) < 300:
            uniques[key] = len(uniques)
    payload = "\n".join(f"{i}\t{d}" for d, i in uniques.items())
    if is_pii_masking_enabled():
        payload = mask_pii(payload)
    try:
        response, model = await generate(quotas, "categorize",
            f"Categorize each bank transaction description. Lines are index<TAB>description.\n{payload}",
            {"system_instruction": "Assign each line one category from the allowed list. 'transfers' means moving money between the person's own accounts or to savings. Return JSON only.",
             "response_mime_type": "application/json", "response_schema": _CatList, "temperature": 0, "max_output_tokens": 8192},
            estimate_tokens(payload) + 4000, timeout_ms=45_000)
        result = _CatList.model_validate(parse_json(response.text))
    except Exception:  # noqa: BLE001 - categorisation is best-effort
        return False, None
    by_index = {c.i: c.category for c in result.items}
    for t in txns:
        cat = by_index.get(uniques.get(t["description"][:80], -1))
        if cat:
            if cat == "income" and t["amount"] < 0:
                cat = "other"
            t["category"] = cat
    return True, model


def _normalize(description: str) -> str:
    d = re.sub(r"[\d#*/_:.,\-]+", " ", description.lower())
    return " ".join(d.split()[:4])


def _add_month(d: date, months: int = 1) -> date:
    month = d.month - 1 + months
    year, month = d.year + month // 12, month % 12 + 1
    for day in (d.day, 30, 29, 28):
        try:
            return date(year, month, day)
        except ValueError:
            continue
    return date(year, month, 28)


def detect_recurring(txns: list[dict], today: date) -> list[Recurring]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for t in txns:
        if t["amount"] < 0 and t.get("category") not in ("transfers", "cash", "income"):
            key = _normalize(t["description"])
            if key:
                groups[key].append(t)
    out = []
    for key, items in groups.items():
        months = {(t["date"].year, t["date"].month) for t in items}
        if len(months) < 2:
            continue
        amounts = [-t["amount"] for t in items]
        median = int(statistics.median(amounts))
        if median <= 0 or any(abs(a - median) > median * 0.15 for a in amounts):
            continue
        last = max(t["date"] for t in items)
        due = _add_month(last)
        while due < today:
            due = _add_month(due)
        cat = items[0].get("category", "other")
        kind = "rent" if cat == "housing" else "debt" if cat == "debt" else "living" if cat in ("utilities", "groceries", "health", "subscriptions") else "other"
        label = max(items, key=lambda t: t["date"])["description"][:60]
        out.append(Recurring(id="rec-" + hashlib.sha1(key.encode()).hexdigest()[:10], label=label, amount=median,
                             next_due=due, occurrences=len(items), kind=kind))
    return sorted(out, key=lambda r: -r.amount)[:15]


# ---------- Gemini document reading ----------

class _AiTxn(BaseModel):
    date: str = Field(description="YYYY-MM-DD")
    description: str
    amount: float = Field(description="Signed: money in positive, money out negative")
    category: Category


class _AiStatement(BaseModel):
    currency: str | None = None
    opening_balance: float | None = None
    closing_balance: float | None = None
    transactions: list[_AiTxn]


DOC_PROMPT = ("Extract every transaction from this bank or card statement. Use the booking date (YYYY-MM-DD). "
              "Amounts are signed: money received is positive, money spent or sent is negative. Include fees. "
              "Do not invent rows. Give the statement's opening and closing balance if printed. "
              "'transfers' means moving money between the person's own accounts or to savings. Return JSON only.")


async def ai_read(data: bytes, mime: str, quotas: Quotas, text: str | None = None) -> tuple[list[dict], dict, str]:
    if text is None and enabled() and not raw_document_ai_allowed():
        raise ImportError_("Raw document AI is disabled while PII masking is enabled.")
    from google.genai import types
    safe_text = mask_pii(text) if text is not None and is_pii_masking_enabled() else text
    contents = [DOC_PROMPT, safe_text] if safe_text is not None else [types.Part.from_bytes(data=data, mime_type=mime), DOC_PROMPT]
    tokens = estimate_tokens(safe_text) if safe_text is not None else max(4000, min(60_000, len(data) // 50))
    response, model = await generate(quotas, "document", contents,
        {"response_mime_type": "application/json", "response_schema": _AiStatement, "temperature": 0, "max_output_tokens": 16384},
        tokens + 8000, timeout_ms=90_000)
    statement = _AiStatement.model_validate(parse_json(response.text))
    rows = []
    for t in statement.transactions:
        d = parse_any_date(t.date)
        cents = parse_amount(t.amount, False)
        if d and cents:
            rows.append({"date": d, "description": (t.description.strip() or "Transaction")[:200], "amount": cents,
                         "category": t.category, "balance": None})
    meta = {"currency": (statement.currency or "EUR").upper()[:3],
            "opening": parse_amount(statement.opening_balance, False) if statement.opening_balance is not None else None,
            "closing": parse_amount(statement.closing_balance, False) if statement.closing_balance is not None else None}
    return rows, meta, model


# ---------- entry point ----------

def file_type(filename: str, content_type: str | None, data: bytes = b"") -> str:
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    if data.startswith(b"%PDF") or name.endswith(".pdf") or "pdf" in ctype:
        return "pdf"
    if data.startswith(b"PK\x03\x04") or name.endswith((".xlsx", ".xlsm")) or "spreadsheet" in ctype or "excel" in ctype:
        return "xlsx"
    if (data.startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF8")) or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
            or name.endswith((".png", ".jpg", ".jpeg", ".webp", ".heic")) or ctype.startswith("image/")):
        return "image"
    if name.endswith((".csv", ".txt", ".tsv", ".tab")) or ctype in ("text/csv", "text/plain", "text/tab-separated-values", "application/csv", "application/vnd.ms-excel"):
        return "csv"
    # Sniff unknown binary/octet-stream payloads: if mostly printable text, treat as CSV/text.
    if data:
        sample = data[:4096]
        if b"\x00" not in sample:
            return "csv"
    raise ImportError_("Upload a CSV, Excel (.xlsx), PDF or image of a statement.")


async def build_preview(data: bytes, filename: str, content_type: str | None, quotas: Quotas, today: date, preview_id: str,
                        *, external_ai_allowed: bool | None = None) -> ImportPreview:
    if not data:
        raise ImportError_("This file is empty.")
    if len(data) > MAX_BYTES:
        raise ImportError_("Files up to 15 MB are supported.")
    kind = file_type(filename, content_type, data)
    warnings: list[str] = []
    parser, model, meta = "local", None, {"currency": "EUR", "opening": None, "closing": None}
    rows: list[dict] = []
    can_ai = enabled() and external_ai_allowed is not False
    try:
        if kind in ("csv", "xlsx"):
            try:
                table = csv_rows(decode(data)) if kind == "csv" else xlsx_rows(data)
                rows, warnings, meta["closing"] = tabular(table, filename)
                header_index = find_header(table)
                if header_index is not None:
                    header = [str(c).strip().lower() for c in table[header_index]]
                    if 'currency' in header:
                        col = header.index('currency')
                        currencies = {r[col].strip().upper() for r in table[header_index+1:] if len(r) > col and r[col].strip()}
                        if len(currencies) > 1:
                            raise ImportError_('Mixed currencies need separate statements; no conversion was applied.')
                        if currencies:
                            meta['currency'] = next(iter(currencies))
            except Exception as local_error:
                if not can_ai:
                    raise ImportError_(str(local_error)) from local_error
                warnings.append("Unusual table layout — read with Gemini AI.")
                text = decode(data) if kind == "csv" else "\n".join(";".join(r) for r in xlsx_rows(data))
                rows, meta, model = await ai_read(b"", "text/plain", quotas, text=text[:250_000])
                parser = "gemini"
            if parser == "local":
                for r in rows:
                    r["category"] = keyword_category(r["description"], r["amount"])
                ok, model = await ai_categorize(rows, quotas) if can_ai else (False, None)
                if not ok:
                    warnings.append("Categories were guessed from keywords.")
        elif kind == "pdf":
            extracted = pdf_text(data)
            allow_raw = raw_document_ai_allowed() and external_ai_allowed is not False
            if external_ai_allowed is False:
                rows = parse_pdf_lines(extracted)
                for r in rows:
                    r['category'] = keyword_category(r['description'], r['amount'])
            elif enabled() and not allow_raw:
                warnings.append("Raw PDF was not sent to Gemini; locally extracted text was masked before AI processing.")
            try:
                if external_ai_allowed is False:
                    if not rows:
                        raise ImportError_('This PDF needs external processing permission or a supported text layout.')
                elif len(extracted) >= 80:
                    rows, meta, model = await ai_read(b"", "text/plain", quotas, text=extracted[:250_000])
                elif allow_raw or not enabled():
                    rows, meta, model = await ai_read(data, "application/pdf", quotas)
                else:
                    rows = parse_pdf_lines(extracted)
                    for r in rows:
                        r["category"] = keyword_category(r["description"], r["amount"])
                parser = "gemini" if model is not None else "local"
            except Exception as pdf_error:
                if len(extracted) >= 80 and allow_raw and external_ai_allowed is not False:
                    try:
                        rows, meta, model = await ai_read(data, "application/pdf", quotas)
                        parser = "gemini"
                    except Exception:
                        pass
                if not rows and extracted:
                    rows = parse_pdf_lines(extracted)
                    for r in rows:
                        r["category"] = keyword_category(r["description"], r["amount"])
                    if rows:
                        warnings.append("Extracted from PDF text locally.")
                if not rows:
                    if isinstance(pdf_error, AIUnavailable):
                        raise
                    raise ImportError_("No transactions found in this PDF.") from pdf_error
        else:
            if external_ai_allowed is False:
                raise ImportError_('Image processing requires explicit external-AI permission.')
            if enabled() and not raw_document_ai_allowed():
                raise ImportError_("Image import requires ALLOW_RAW_DOCUMENT_AI=true while PII masking is enabled.")
            mime = content_type if (content_type or "").startswith("image/") else "image/jpeg"
            rows, meta, model = await ai_read(data, mime, quotas)
            parser = "gemini"
    except AIUnavailable as exc:
        raise ImportError_(str(exc)) from exc
    if not rows:
        raise ImportError_("No transactions found in this file.")
    if meta["currency"] not in ("EUR", "", None):
        warnings.append(f"This statement looks like {meta['currency']}. No conversion was applied; EUR-only analysis cannot save it.")
    if meta["opening"] is not None and meta["closing"] is not None:
        expected = meta["opening"] + sum(r["amount"] for r in rows)
        if abs(expected - meta["closing"]) > 100:
            warnings.append(f"Opening balance plus transactions differs from the closing balance by €{abs(expected-meta['closing'])/100:,.2f}. Some rows may be missing — check before applying.")
    source = f"import:{filename[:80]}"
    txns = []
    for r in rows:
        # Preserve explicit refund labels even when best-effort AI guessed income.
        if keyword_category(r['description'], r['amount']) == 'refunds':
            r['category'] = 'refunds'
        digest = hashlib.sha1(f"{r['date']}|{r['amount']}|{r['description']}".encode()).hexdigest()[:16]
        txns.append(Transaction(id=f"t-{digest}", date=r["date"], description=r["description"], amount=r["amount"],
                                category=r.get("category") if r.get("category") in CATEGORIES else "other", source=source))
    dates = [t.date for t in txns]
    real = [t for t in txns if t.category != "transfers"]
    return ImportPreview(id=preview_id, filename=filename[:120], file_type=kind, parser=parser, model=model,
                         currency=meta["currency"] or "EUR", period_start=min(dates), period_end=max(dates),
                         opening_balance=meta["opening"], closing_balance=meta["closing"],
                         income=sum(t.amount for t in real if t.amount > 0 and t.category != 'refunds'),
                         spending=sum(-t.amount for t in real if t.amount < 0),
                         refunds=sum(t.amount for t in real if t.amount > 0 and t.category == 'refunds'),
                         net_spending=sum(-t.amount for t in real if t.amount < 0)-sum(t.amount for t in real if t.amount > 0 and t.category == 'refunds'),
                         transactions=txns, recurring=detect_recurring(rows, today), warnings=warnings,
                         source_checksum=hashlib.sha256(data).hexdigest(),
                         source_rows=[SourceRow(ordinal=i+1,date=r['date'],amount=r['amount'],currency=meta['currency'] or 'EUR',
                            description=r['description'],category=txns[i].category,
                            category_method='parser_output_or_keyword',
                            bank_reference=r.get('bank_reference'),booking_status=r.get('booking_status')) for i,r in enumerate(rows)])
