"""Autonomous PII masking module for privacy-preserving AI calls and statements."""
from __future__ import annotations

import os
import re
from typing import Sequence

# ---------------------------------------------------------------------------
# Configuration and Environment
# ---------------------------------------------------------------------------

def is_pii_masking_enabled() -> bool:
    """Check if PII masking is enabled via PII_MASKING environment variable.

    Defaults to True unless set to 'false', '0', 'no', or 'off'.
    """
    val = os.getenv("PII_MASKING", "true").strip().lower()
    return val not in ("false", "0", "no", "off")


# ---------------------------------------------------------------------------
# Validation Helpers: IBAN and Luhn
# ---------------------------------------------------------------------------

def is_valid_iban(raw: str) -> bool:
    """Validate International Bank Account Number using ISO 7064 MOD 97-10 check.

    Length must be between 15 and 34 characters (excluding spaces),
    starting with 2 uppercase letters and 2 check digits.
    """
    cleaned = "".join(raw.split()).upper()
    if not (15 <= len(cleaned) <= 34):
        return False
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$", cleaned):
        return False

    rearranged = cleaned[4:] + cleaned[:4]
    digits = []
    for ch in rearranged:
        if ch.isdigit():
            digits.append(ch)
        elif "A" <= ch <= "Z":
            digits.append(str(ord(ch) - 55))
        else:
            return False
    try:
        return int("".join(digits)) % 97 == 1
    except ValueError:
        return False


def is_valid_luhn(card_number: str) -> bool:
    """Validate payment card Primary Account Number (PAN) using Luhn algorithm.

    Length must be between 13 and 19 digits. All-zeros or leading zero
    are not valid issuer payment card numbers.
    """
    digits = [int(c) for c in card_number if c.isdigit()]
    if not (13 <= len(digits) <= 19):
        return False
    if digits[0] == 0 or all(d == 0 for d in digits):
        return False

    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled if doubled < 10 else doubled - 9
        else:
            checksum += digit
    return checksum % 10 == 0


# ---------------------------------------------------------------------------
# Compiled Regular Expressions
# ---------------------------------------------------------------------------

# Statement headers: Name & Address
# Handles prefixes in DE/EN/RU, preceded by start of line, comma, semicolon, tab, pipe
NAME_HEADER_RE = re.compile(
    r"(?im)(?:^|(?<=[\r\n;\|\t,]))"
    r"([ \t]*(?:Account\s+holder|Kontoinhaber|Владелец\s+сч[её]та)[ \t]*[:;][ \t]*)"
    r"([^;\r\n\|\t]+?)"
    r"(?=\s*,\s*(?:Account|Kontoinhaber|Владелец|Address|Adresse|Адрес|IBAN|BIC|Bank|Phone|Tel|Email\b)|[;\r\n\|\t]|$)",
    re.UNICODE,
)

ADDR_HEADER_RE = re.compile(
    r"(?im)(?:^|(?<=[\r\n;\|\t,]))"
    r"([ \t]*(?:Address|Adresse|Адрес)[ \t]*[:;][ \t]*)"
    r"([^;\r\n\|\t]+?)"
    r"(?=\s*,\s*(?:Account|Kontoinhaber|Владелец|Address|Adresse|Адрес|IBAN|BIC|Bank|Phone|Tel|Email\b)|[;\r\n\|\t]|$)",
    re.UNICODE,
)

# IBAN pattern: 15-34 chars, 4-char groups or continuous
IBAN_RE = re.compile(
    r"\b[A-Za-z]{2}\d{2}(?:[ \t]?[A-Za-z0-9]{4}){2,7}(?:[ \t]?[A-Za-z0-9]{1,4})?\b|"
    r"\b[A-Za-z]{2}\d{2}[A-Za-z0-9]{11,30}\b"
)

# Card numbers are matched by explicit layouts. A broad "digits and spaces"
# expression can consume the amount in `PAN 1200.50 EUR` and make a valid PAN
# fail Luhn validation. Longest layouts run first so shorter patterns cannot
# partially redact a valid 19-digit PAN.
CARD_PATTERNS = (
    re.compile(r"(?<![\d+])(?:\d{4}[ -]){4}\d{3}(?!\d)"),  # 4-4-4-4-3
    re.compile(r"(?<![\d+])\d{4}[ -]\d{6}[ -]\d{5}(?!\d)"),  # Amex 4-6-5
    re.compile(r"(?<![\d+])\d{4}[ -]\d{6}[ -]\d{4}(?!\d)"),  # Diners 4-6-4
    re.compile(r"(?<![\d+])(?:\d{4}[ -]){3}\d{6}(?!\d)"),  # 4-4-4-6
    re.compile(r"(?<![\d+])(?:\d{4}[ -]){3}\d{5}(?!\d)"),  # 4-4-4-5
    re.compile(r"(?<![\d+])(?:\d{4}[ -]){3}\d{4}(?!\d)"),  # 4-4-4-4
    re.compile(r"(?<![\d+])(?:\d{4}[ -]){3}\d{3}(?!\d)"),  # 4-4-4-3
    re.compile(r"(?<![\d+])(?:\d{4}[ -]){3}\d{2}(?!\d)"),  # 4-4-4-2
    re.compile(r"(?<![\d+])(?:\d{4}[ -]){3}\d(?!\d)"),  # 4-4-4-1
    re.compile(r"(?<![\d+])\d{13,19}(?!\d)"),  # continuous
)

# Email address
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# International phone numbers: +XX... or 00XX... (9 to 15 digits)
# Broken down by standard international representations to avoid greedy swallowing
# of adjacent amounts or misidentifying currency amounts and dates.
PHONE_PATTERNS = [
    # 1. Dotted notation: +49.170.123.45.67 (no spaces allowed)
    re.compile(r"(?<![A-Za-z0-9])(?:\+|00)[1-9]\d{0,3}(?:\.\d{1,8}){2,6}(?!\d)(?![,\.]\d)"),
    # 2. Slashed notation: +49/170/1234567
    re.compile(r"(?<![A-Za-z0-9])(?:\+|00)[1-9]\d{0,3}(?:/\d{1,8}){1,4}(?!\d)(?![,\.]\d)"),
    # 3. Hyphenated notation: +1-800-555-0199 or +49-170-1234567
    re.compile(r"(?<![A-Za-z0-9])(?:\+|00)[1-9]\d{0,3}(?:-\d{1,8}){1,5}(?!\d)(?![,\.]\d)"),
    # 4. Spaced/parenthesized notation: +49 170 1234567, +7 (999) 123-45-67, +49 (0) 170 1234567
    re.compile(
        r"(?<![A-Za-z0-9])(?:\+|00)[1-9]\d{0,3}"
        r"(?:[ \-]| \(\d{1,4}\) |-\(\d{1,4}\)-|\(\d{1,4}\))"
        r"(?:[ \-]?(?!\d+[,\.]\d)\d{1,8}){1,5}(?!\d)(?![,\.]\d)"
    ),
    # 5. Continuous: +491701234567, 00491701234567
    re.compile(r"(?<![A-Za-z0-9])(?:\+|00)[1-9]\d{8,14}(?!\d)(?![,\.]\d)"),
]

_CURRENCY_AHEAD_RE = re.compile(
    r"^(?:EUR|USD|GBP|RUB|CHF|€|\$|£|cents?|rubles?|евро|руб)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Core Masking Implementation
# ---------------------------------------------------------------------------

def mask_pii(text: str, *, force: bool = False) -> str:
    """Mask Personally Identifiable Information (PII) in text.

    Redacts:
    - Statement header names (Account holder:, Kontoinhaber:, Владелец счёта:) -> [REDACTED_NAME]
    - Statement header addresses (Address:, Adresse:, Адрес:) -> [REDACTED_ADDRESS]
    - Valid IBANs (mod 97 == 1) -> [REDACTED_IBAN]
    - Payment card numbers (Luhn check) -> [REDACTED_CARD]
    - Email addresses -> [REDACTED_EMAIL]
    - International phone numbers (+XX..., 00XX..., 9-15 digits) -> [REDACTED_PHONE]

    Preserves dates, monetary amounts, and merchant names.
    If PII_MASKING is disabled and force is False, returns text unchanged.
    """
    if not force and not is_pii_masking_enabled():
        return text

    # 1. Statement header names & addresses
    def _repl_name(m: re.Match) -> str:
        if not m.group(2).strip():
            return m.group(0)
        return f"{m.group(1)}[REDACTED_NAME]"

    def _repl_addr(m: re.Match) -> str:
        if not m.group(2).strip():
            return m.group(0)
        return f"{m.group(1)}[REDACTED_ADDRESS]"

    text = NAME_HEADER_RE.sub(_repl_name, text)
    text = ADDR_HEADER_RE.sub(_repl_addr, text)

    # 2. IBAN
    def _repl_iban(m: re.Match) -> str:
        raw = m.group(0)
        if is_valid_iban(raw):
            return "[REDACTED_IBAN]"
        return raw

    text = IBAN_RE.sub(_repl_iban, text)

    # 3. Card numbers (Luhn check)
    def _repl_card(m: re.Match) -> str:
        raw = m.group(0)
        digits = [c for c in raw if c.isdigit()]
        if not (13 <= len(digits) <= 19):
            return raw
        if is_valid_luhn(raw):
            return "[REDACTED_CARD]"
        return raw

    for pattern in CARD_PATTERNS:
        text = pattern.sub(_repl_card, text)

    # 4. Email addresses
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)

    # 5. Phone numbers (+XX... or 00XX..., 9 to 15 digits)
    for pat in PHONE_PATTERNS:
        def _repl_phone(m: re.Match, cur_text: str = text) -> str:
            cand = m.group(0)
            digits = [c for c in cand if c.isdigit()]
            if cand.startswith("00"):
                digits = digits[2:]
            if not (9 <= len(digits) <= 15):
                return cand
            trailing = cur_text[m.end() : m.end() + 15].strip()
            if _CURRENCY_AHEAD_RE.match(trailing):
                return cand
            return "[REDACTED_PHONE]"

        text = pat.sub(_repl_phone, text)

    return text


def mask_pii_lines(lines: Sequence[str], *, force: bool = False) -> list[str]:
    """Apply mask_pii to each line in the given sequence."""
    return [mask_pii(line, force=force) for line in lines]
