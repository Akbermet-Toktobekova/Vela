"""CSV Formula Injection Defense (CSV / DDE Injection).

Mitigates formula injection attacks when exporting tabular financial data to CSV.
Spreadsheet software (Microsoft Excel, LibreOffice Calc, Google Sheets, Apple Numbers)
interprets cells starting with '=', '+', '-', '@', '\t', or '\r' as formulas or commands.
If an attacker inserts a payload like '=cmd|' /C calc'!A0' into a merchant name, description,
or category, opening the exported CSV can execute arbitrary commands or exfiltrate data.

To prevent this, any string cell starting with these characters (unless it is a pure, safe
number like -42 or +100) is prepended with a single quote ('') which forces spreadsheet
software to render the content as literal text.
"""

from collections.abc import Sequence
import csv
import io
import re
from typing import Any

# Characters that trigger formula evaluation or DDE commands in spreadsheet software
DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

# Strict regex matching pure integer or decimal numbers (with dot or comma), without arithmetic operators or commands
_NUMBER_RE = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")


def is_pure_number(value: object) -> bool:
    """Checks if a value is purely numeric (integer or decimal), not an expression or formula."""
    if isinstance(value, (int, float)):
        return True
    if not isinstance(value, str):
        return False
    return bool(_NUMBER_RE.match(value.strip()))


def escape_cell(value: Any) -> str:
    """Escapes a single cell value against CSV formula injection.

    If the value starts with '=', '+', '-', '@', '\t', or '\r' and is not a pure
    number, an apostrophe (') is prepended. Pure positive/negative numbers are
    preserved as-is without distortion.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)

    s = str(value)
    if not s:
        return ""

    stripped = s.lstrip()
    if s.startswith(DANGEROUS_PREFIXES) or (stripped and stripped[0] in ("=", "@")):
        if is_pure_number(s):
            return s
        return f"'{s}"

    return s


def escape_row(row: Sequence[Any]) -> list[str]:
    """Escapes each cell in a row against formula injection."""
    return [escape_cell(cell) for cell in row]


def escape_table(rows: Sequence[Sequence[Any]]) -> list[list[str]]:
    """Escapes all cells in a 2D table of rows."""
    return [escape_row(row) for row in rows]


def format_safe_csv(rows: Sequence[Sequence[Any]], delimiter: str = ",", lineterminator: str = "\r\n") -> str:
    """Renders a 2D table into safe CSV text with RFC 4180 compatibility and formula escaping."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter, lineterminator=lineterminator)
    for row in rows:
        writer.writerow(escape_row(row))
    return buf.getvalue()
