"""Autonomous chat tools and post-generation numeric verification module (§9, §10, §15).

Provides 4 pure deterministic tools for grounding AI chat responses in verified domain state:
1. `get_financial_snapshot(state) -> dict`: cash, buffer, capacity, 30d bills, planned step.
2. `calculate_cash_flow(state, days) -> dict`: income, spending, net flow, min projected balance.
3. `simulate_debt_payment(state, extra) -> dict`: portfolio summary, Avalanche vs Snowball.
4. `get_spending_by_category(state, limit) -> dict`: top categories, 30d subscriptions.

Also provides `verify_reply_numbers(reply_text, tool_outputs) -> tuple[bool, list[str]]`
to detect hallucinated monetary figures or ungrounded percentages in generated replies.
All financial arithmetic uses integer EUR cents (`int`, never `float`).
"""

from collections import defaultdict
from collections.abc import Sequence
from datetime import date, timedelta
import re
from typing import Any

from .debt import DebtSimulationView, StrategyResult, compare_and_simulate
from .domain import Debt, Obligation, Snapshot, State, StateView, Transaction, capacity, format_eur


# Whitelist of trivial integer constants (days, cooldowns, small counts, common horizons)
ALLOWED_PLAIN_CONSTANTS: frozenset[int] = frozenset({
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    12, 14, 15, 20, 24, 28, 29, 30, 31,
    60, 90, 93, 100, 180, 365,
})


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Safe getter supporting both dictionary and attribute-based objects."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _parse_date(val: Any) -> date | None:
    if val is None or isinstance(val, date):
        return val
    if isinstance(val, str):
        return date.fromisoformat(val)
    return None


def get_financial_snapshot(state: State | StateView | dict | Any) -> dict:
    """Extracts verified balance, buffer, available capacity, 30-day obligations,

    and active planned steps in integer EUR cents and formatted EUR strings.
    Supports State, StateView, or dictionary representations.
    """
    s = _get(state, "snapshot", None)
    if s is None:
        return {
            "has_snapshot": False,
            "balance_cents": 0,
            "balance_eur": format_eur(0),
            "protected_buffer_cents": 0,
            "protected_buffer_eur": format_eur(0),
            "available_cents": 0,
            "available_eur": format_eur(0),
            "obligations_30d_cents": 0,
            "obligations_30d_eur": format_eur(0),
            "obligations_30d": [],
            "obligations_total_cents": 0,
            "obligations_total_eur": format_eur(0),
            "planned_step_cents": 0,
            "planned_step_eur": format_eur(0),
            "saved_cents": 0,
            "saved_eur": format_eur(0),
            "goal_target_cents": 0,
            "goal_target_eur": format_eur(0),
            "goal_remaining_cents": 0,
            "goal_remaining_eur": format_eur(0),
            "goal_name": "",
            "as_of": None,
            "horizon": None,
            "obligations_complete": False,
            "debt_known": False,
        }

    as_of = _parse_date(_get(s, "as_of")) or date.today()
    horizon = _parse_date(_get(s, "horizon")) or as_of
    cash = _get(s, "cash", 0)
    protected = _get(s, "protected", 0)
    saved = _get(s, "saved", 0)
    goal_target = _get(s, "goal_target", 0)
    goal_name = _get(s, "goal_name", "")
    obligations_complete = bool(_get(s, "obligations_complete", False))
    debt_known = bool(_get(s, "debt_known", False))

    raw_obs = _get(s, "obligations", [])
    cutoff_30d = as_of + timedelta(days=30)

    obs_30d = []
    obs_total_cents = 0
    obs_30d_cents = 0

    for o in raw_obs:
        amt = _get(o, "amount", 0)
        due = _parse_date(_get(o, "due")) or as_of
        obs_total_cents += amt
        if as_of <= due <= cutoff_30d:
            obs_30d_cents += amt
            obs_30d.append({
                "id": _get(o, "id", ""),
                "label": _get(o, "label", ""),
                "amount_cents": amt,
                "amount_eur": format_eur(amt),
                "due": due.isoformat(),
                "kind": _get(o, "kind", "other"),
            })

    obs_30d.sort(key=lambda item: (item["due"], item["id"]))

    actions = _get(state, "actions", [])
    planned_step_cents = sum(_get(a, "amount", 0) for a in actions if _get(a, "status") == "planned")

    if isinstance(state, State):
        avail_cents = capacity(state)
    elif isinstance(state, dict) and "available" in state:
        avail_cents = state["available"]
    elif hasattr(state, "available"):
        avail_cents = getattr(state, "available")
    else:
        avail_cents = cash - saved - protected - planned_step_cents - obs_total_cents

    goal_rem_cents = max(0, goal_target - saved)

    return {
        "has_snapshot": True,
        "balance_cents": cash,
        "balance_eur": format_eur(cash),
        "protected_buffer_cents": protected,
        "protected_buffer_eur": format_eur(protected),
        "available_cents": avail_cents,
        "available_eur": format_eur(avail_cents),
        "obligations_30d_cents": obs_30d_cents,
        "obligations_30d_eur": format_eur(obs_30d_cents),
        "obligations_30d": obs_30d,
        "obligations_total_cents": obs_total_cents,
        "obligations_total_eur": format_eur(obs_total_cents),
        "planned_step_cents": planned_step_cents,
        "planned_step_eur": format_eur(planned_step_cents),
        "saved_cents": saved,
        "saved_eur": format_eur(saved),
        "goal_target_cents": goal_target,
        "goal_target_eur": format_eur(goal_target),
        "goal_remaining_cents": goal_rem_cents,
        "goal_remaining_eur": format_eur(goal_rem_cents),
        "goal_name": goal_name,
        "as_of": as_of.isoformat(),
        "horizon": horizon.isoformat(),
        "obligations_complete": obligations_complete,
        "debt_known": debt_known,
    }


def calculate_cash_flow(state: State | StateView | dict | Any, days: int = 30) -> dict:
    """Computes verified income, spending, net cash flow, and minimum projected balance

    over the specified window (default 30 days) in integer EUR cents and formatted EUR.
    """
    raw_txns = _get(state, "transactions", [])
    min_projected_cents = capacity(state) if isinstance(state, State) and state.snapshot is not None else _get(state, "available", 0)
    min_projected_eur = format_eur(min_projected_cents)

    if not raw_txns:
        return {
            "days": days,
            "transaction_count": 0,
            "period_start": None,
            "period_end": None,
            "income_cents": 0,
            "income_eur": format_eur(0),
            "spending_cents": 0,
            "spending_eur": format_eur(0),
            "net_cash_flow_cents": 0,
            "net_cash_flow_eur": format_eur(0),
            "min_projected_balance_cents": min_projected_cents,
            "min_projected_balance_eur": min_projected_eur,
        }

    txns = [t if isinstance(t, Transaction) else Transaction(**t) for t in raw_txns]
    end = max(t.date for t in txns)
    start = end - timedelta(days=max(1, days) - 1)
    recent = [t for t in txns if t.date >= start]

    income_cents = sum(t.amount for t in recent if t.amount > 0 and t.category != "transfers")
    spending_cents = sum(-t.amount for t in recent if t.amount < 0 and t.category != "transfers")
    net_flow_cents = income_cents - spending_cents

    return {
        "days": days,
        "transaction_count": len(recent),
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "income_cents": income_cents,
        "income_eur": format_eur(income_cents),
        "spending_cents": spending_cents,
        "spending_eur": format_eur(spending_cents),
        "net_cash_flow_cents": net_flow_cents,
        "net_cash_flow_eur": format_eur(net_flow_cents),
        "min_projected_balance_cents": min_projected_cents,
        "min_projected_balance_eur": min_projected_eur,
    }


def simulate_debt_payment(state: State | StateView | dict | Any, extra_payment_cents: int = 0) -> dict:
    """Simulates debt payoff strategies (minimum_only baseline, Avalanche, Snowball)

    via `debt.compare_and_simulate` with optional one-off extra payment preview.
    """
    raw_debts = _get(state, "debts", [])
    if not raw_debts:
        return {
            "has_debts": False,
            "debt_count": 0,
            "total_balance_cents": 0,
            "total_balance_eur": format_eur(0),
            "total_min_payment_cents": 0,
            "total_min_payment_eur": format_eur(0),
            "status": "none",
            "baseline": None,
            "avalanche": None,
            "snowball": None,
            "one_off_preview": None,
            "debts": [],
        }

    debts = [d if isinstance(d, Debt) else Debt(**d) for d in raw_debts]
    total_balance = sum(d.balance_cents for d in debts)
    total_min_payment = sum(d.min_payment_cents for d in debts)

    sim: DebtSimulationView = compare_and_simulate(
        debts=debts,
        revision=_get(state, "revision", 0),
        recurring_extra_cents=0,
        one_off_extra_cents=extra_payment_cents,
    )

    def _format_strategy(strat: StrategyResult) -> dict:
        return {
            "strategy": strat.strategy,
            "status": strat.status,
            "months": strat.months,
            "total_interest_cents": strat.total_interest_cents,
            "total_interest_eur": format_eur(strat.total_interest_cents) if strat.total_interest_cents is not None else None,
            "total_paid_cents": strat.total_paid_cents,
            "total_paid_eur": format_eur(strat.total_paid_cents) if strat.total_paid_cents is not None else None,
            "interest_saved_cents": strat.interest_saved_vs_baseline_cents,
            "interest_saved_eur": format_eur(strat.interest_saved_vs_baseline_cents) if strat.interest_saved_vs_baseline_cents is not None else None,
            "months_saved": strat.months_saved_vs_baseline,
        }

    one_off_dict = None
    if sim.one_off_preview and extra_payment_cents > 0:
        p = sim.one_off_preview
        one_off_dict = {
            "requested_extra_cents": p.requested_extra_cents,
            "requested_extra_eur": format_eur(p.requested_extra_cents),
            "applied_extra_cents": p.applied_extra_cents,
            "applied_extra_eur": format_eur(p.applied_extra_cents),
            "status": p.status,
            "months": p.months,
            "total_interest_cents": p.total_interest_cents,
            "total_interest_eur": format_eur(p.total_interest_cents) if p.total_interest_cents is not None else None,
            "total_paid_cents": p.total_paid_cents,
            "total_paid_eur": format_eur(p.total_paid_cents) if p.total_paid_cents is not None else None,
            "interest_saved_cents": p.interest_saved_cents,
            "interest_saved_eur": format_eur(p.interest_saved_cents) if p.interest_saved_cents is not None else None,
            "months_saved": p.months_saved,
        }

    debts_summary = [
        {
            "id": d.id,
            "label": d.label,
            "balance_cents": d.balance_cents,
            "balance_eur": format_eur(d.balance_cents),
            "apr_bps": d.apr_bps,
            "apr_percent": f"{d.apr_bps / 100:.2f}%" if d.apr_bps % 100 != 0 else f"{d.apr_bps // 100}%",
            "min_payment_cents": d.min_payment_cents,
            "min_payment_eur": format_eur(d.min_payment_cents),
            "due_day": d.due_day,
            "kind": d.kind,
            "terms_known": d.terms_known,
        }
        for d in debts
    ]

    return {
        "has_debts": True,
        "debt_count": len(debts),
        "total_balance_cents": total_balance,
        "total_balance_eur": format_eur(total_balance),
        "total_min_payment_cents": total_min_payment,
        "total_min_payment_eur": format_eur(total_min_payment),
        "status": sim.status,
        "baseline": _format_strategy(sim.baseline),
        "avalanche": _format_strategy(sim.avalanche),
        "snowball": _format_strategy(sim.snowball),
        "one_off_preview": one_off_dict,
        "debts": debts_summary,
    }


def get_spending_by_category(state: State | StateView | dict | Any, limit: int = 5) -> dict:
    """Computes top spending categories and recurring subscription charges over

    the last 30 days of data in integer EUR cents and formatted EUR.
    """
    raw_txns = _get(state, "transactions", [])
    if not raw_txns:
        return {
            "period_start": None,
            "period_end": None,
            "total_spending_cents": 0,
            "total_spending_eur": format_eur(0),
            "top_categories": [],
            "subscriptions": [],
            "subscriptions_total_cents": 0,
            "subscriptions_total_eur": format_eur(0),
        }

    txns = [t if isinstance(t, Transaction) else Transaction(**t) for t in raw_txns]
    end = max(t.date for t in txns)
    start = end - timedelta(days=29)
    recent = [t for t in txns if t.date >= start and t.category != "transfers" and t.amount < 0]

    by_cat: dict[str, int] = defaultdict(int)
    for t in recent:
        by_cat[t.category] += -t.amount

    top = sorted(by_cat.items(), key=lambda kv: -kv[1])[:limit]
    top_categories = [
        {"category": c, "amount_cents": a, "amount_eur": format_eur(a)}
        for c, a in top
    ]

    subs = [t for t in recent if t.category == "subscriptions"]
    subs_total_cents = sum(-t.amount for t in subs)
    subscriptions = [
        {
            "id": t.id,
            "description": t.description,
            "amount_cents": -t.amount,
            "amount_eur": format_eur(-t.amount),
            "date": t.date.isoformat(),
        }
        for t in sorted(subs, key=lambda t: (t.date, t.id), reverse=True)
    ]

    total_spending_cents = sum(-t.amount for t in recent)

    return {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "total_spending_cents": total_spending_cents,
        "total_spending_eur": format_eur(total_spending_cents),
        "top_categories": top_categories,
        "subscriptions": subscriptions,
        "subscriptions_total_cents": subs_total_cents,
        "subscriptions_total_eur": format_eur(subs_total_cents),
    }


def collect_all_tool_outputs(state: State | StateView | dict | Any) -> dict:
    """Gathers outputs from all 4 deterministic tools into a unified grounding dictionary."""
    return {
        "snapshot": get_financial_snapshot(state),
        "cash_flow": calculate_cash_flow(state, days=30),
        "debt": simulate_debt_payment(state),
        "spending": get_spending_by_category(state, limit=5),
    }


def extract_tool_numbers(data: Any) -> tuple[set[int], set[float], set[int]]:
    """Traverses nested tool outputs and extracts sets of:

    1. `valid_cents`: all monetary figures expressed in integer EUR cents.
    2. `valid_percents`: all percentages (e.g. APRs from bps, discount rates).
    3. `valid_counts_or_wholes`: non-monetary integers (days, months, counts, whole EUR).
    """
    valid_cents: set[int] = {0}
    valid_percents: set[float] = {0.0, 100.0}
    valid_counts: set[int] = set()

    def _walk(obj: Any, key_name: str = ""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _walk(v, str(k))
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                _walk(item, key_name)
        elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
            val = obj
            k = key_name.lower()
            if "cent" in k or k in ("cash", "saved", "protected", "amount", "spending", "income"):
                c = int(round(val))
                valid_cents.add(c)
                valid_cents.add(abs(c))
                if c % 100 == 0:
                    valid_counts.add(c // 100)
                    valid_counts.add(abs(c // 100))
            elif "bps" in k:
                pct = round(val / 100.0, 2)
                valid_percents.add(pct)
                valid_counts.add(int(round(val)))
            elif any(sub in k for sub in ("day", "month", "count", "revision", "limit")):
                valid_counts.add(int(round(val)))
            else:
                if isinstance(val, int):
                    valid_counts.add(val)
                    valid_cents.add(val)
                    valid_cents.add(abs(val))
                    if val % 100 == 0:
                        valid_counts.add(val // 100)
                        valid_counts.add(abs(val // 100))
                else:
                    valid_percents.add(round(val, 2))
        elif isinstance(obj, str):
            s = obj.strip()
            # Extract EUR string like "€1,200.50" or "€1,000" or "-€50"
            m_eur = re.search(r"[€EUR]\s*([+-]?[\d,]+(?:\.\d+)?)", s)
            if m_eur:
                num_str = m_eur.group(1).replace(",", "")
                try:
                    c = int(round(float(num_str) * 100))
                    valid_cents.add(c)
                    valid_cents.add(abs(c))
                    if c % 100 == 0:
                        valid_counts.add(c // 100)
                        valid_counts.add(abs(c // 100))
                except ValueError:
                    pass
            # Extract percentage string like "18.5%" or "6%"
            m_pct = re.search(r"([+-]?\d+(?:[.,]\d+)?)\s*%", s)
            if m_pct:
                try:
                    pct = float(m_pct.group(1).replace(",", "."))
                    valid_percents.add(round(pct, 2))
                except ValueError:
                    pass

    _walk(data)
    return valid_cents, valid_percents, valid_counts


def _parse_currency_candidates_to_cents(raw_match: str) -> list[int]:
    """Parses a matched currency string (prefix or suffix) into potential candidate cent amounts."""
    clean = re.sub(r"[€$£\s]", "", raw_match).strip()
    is_cents_unit = bool(re.search(r"cents?\b", clean, flags=re.IGNORECASE))
    clean = re.sub(r"cents?|euros?|euro|eur", "", clean, flags=re.IGNORECASE).strip()

    sign = -1 if ("-" in raw_match or "−" in raw_match) else 1
    clean = clean.replace("+", "").replace("-", "").replace("−", "").strip()

    if not clean:
        return []

    candidates: list[int] = []

    # Format with both comma and dot: e.g. 1,234.56 or 1.234,56
    if "," in clean and "." in clean:
        if clean.rfind(",") > clean.rfind("."):
            num = float(clean.replace(".", "").replace(",", "."))
        else:
            num = float(clean.replace(",", ""))
        cents = int(round(num * 100)) if not is_cents_unit else int(round(num))
        candidates.append(sign * cents)
        return candidates

    # Format with comma only
    if "," in clean:
        parts = clean.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            # Decimal separator: 12,50
            num = float(clean.replace(",", "."))
            cents = int(round(num * 100)) if not is_cents_unit else int(round(num))
            candidates.append(sign * cents)
        else:
            # Thousands separator: 1,000
            num = float(clean.replace(",", ""))
            cents = int(round(num * 100)) if not is_cents_unit else int(round(num))
            candidates.append(sign * cents)
        return candidates

    # Format with dot only
    if "." in clean:
        parts = clean.split(".")
        if len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3:
            # Could be thousand separator (1.000) or decimal (1.000)
            num_th = float(clean.replace(".", ""))
            cents_th = int(round(num_th * 100)) if not is_cents_unit else int(round(num_th))
            candidates.append(sign * cents_th)

            num_dec = float(clean)
            cents_dec = int(round(num_dec * 100)) if not is_cents_unit else int(round(num_dec))
            candidates.append(sign * cents_dec)
            return candidates
        else:
            num = float(clean)
            cents = int(round(num * 100)) if not is_cents_unit else int(round(num))
            candidates.append(sign * cents)
            return candidates

    # Plain integer
    try:
        val = int(clean)
        cents = val if is_cents_unit else val * 100
        candidates.append(sign * cents)
    except ValueError:
        pass

    return candidates


# Regex patterns for currency amounts and percentages
_CURRENCY_PREFIX_RE = re.compile(
    r"(?:€|EUR)\s*[-+−]?\s*(?:\d{1,3}(?:[.,]\d{3})*|\d+)(?:[.,]\d+)?",
    re.IGNORECASE,
)
_CURRENCY_SUFFIX_RE = re.compile(
    r"[-+−]?\s*(?:\d{1,3}(?:[.,]\d{3})*|\d+)(?:[.,]\d+)?\s*(?:€|EUR|euros?|cents?)\b",
    re.IGNORECASE,
)
_PERCENTAGE_RE = re.compile(
    r"[-+−]?\s*\d+(?:[.,]\d+)?\s*%",
)
_DATE_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b|\b\d{1,2}(?:st|nd|rd|th)\b",
    re.IGNORECASE,
)
_PLAIN_NUMBER_RE = re.compile(
    r"\b\d+(?:[.,]\d+)?\b",
)


def verify_reply_numbers(reply_text: str, tool_outputs: dict) -> tuple[bool, list[str]]:
    """Verifies that all monetary amounts, percentages, and numeric figures in `reply_text`

    are strictly grounded in `tool_outputs` or allowed domain constants.

    Returns:
        `(True, [])` if all extracted numbers are confirmed.
        `(False, unconfirmed_list)` if one or more numbers are unconfirmed ("hallucinated").
    """
    if not reply_text:
        return True, []

    valid_cents, valid_percents, valid_counts = extract_tool_numbers(tool_outputs)
    unconfirmed: list[str] = []

    working_text = reply_text

    # 1. Mask known date expressions (e.g. 2026-03-01, 15.03.2026) so date components aren't flagged as money
    def _mask_date(match: re.Match) -> str:
        return " " * len(match.group(0))

    working_text = _DATE_RE.sub(_mask_date, working_text)

    # 2. Mask markdown bullet points like "^1. " or "\n 2. " or "(1)"
    working_text = re.sub(r"(?m)^\s*\d+\.\s+", lambda m: " " * len(m.group(0)), working_text)
    working_text = re.sub(r"\(\d+\)", lambda m: " " * len(m.group(0)), working_text)
    working_text = re.sub(r"§\s*\d+", lambda m: " " * len(m.group(0)), working_text)

    # 3. Check explicit currency figures (prefix: €1000, suffix: 1000 € / 1000 EUR / 50 cents)
    def _check_and_mask_currency(match: re.Match) -> str:
        raw = match.group(0)
        candidates = _parse_currency_candidates_to_cents(raw)
        confirmed = False
        for c in candidates:
            if c in valid_cents or abs(c) in valid_cents:
                confirmed = True
                break
        if not confirmed:
            unconfirmed.append(raw.strip())
        return " " * len(raw)

    working_text = _CURRENCY_PREFIX_RE.sub(_check_and_mask_currency, working_text)
    working_text = _CURRENCY_SUFFIX_RE.sub(_check_and_mask_currency, working_text)

    # 4. Check explicit percentage figures (e.g. 18.5%, 6%)
    def _check_and_mask_percentage(match: re.Match) -> str:
        raw = match.group(0)
        clean = raw.replace("%", "").replace(",", ".").replace("+", "").replace("−", "-").strip()
        try:
            pct = float(clean)
            if any(abs(pct - vp) < 0.05 for vp in valid_percents):
                return " " * len(raw)
        except ValueError:
            pass
        unconfirmed.append(raw.strip())
        return " " * len(raw)

    working_text = _PERCENTAGE_RE.sub(_check_and_mask_percentage, working_text)

    # 5. Check remaining standalone plain numbers
    for m in _PLAIN_NUMBER_RE.finditer(working_text):
        raw = m.group(0)
        clean = raw.replace(",", ".")
        try:
            val_float = float(clean)
        except ValueError:
            continue

        val_int = int(round(val_float)) if abs(val_float - round(val_float)) < 1e-6 else None

        # Check whitelist of plain constants (counts, durations like 14, 30, 93) or year (2020..2035)
        if val_int is not None and (val_int in ALLOWED_PLAIN_CONSTANTS or 2020 <= val_int <= 2035):
            continue

        # Check if matches valid non-monetary count/month/day/revision from tool_outputs
        if val_int is not None and (val_int in valid_counts or abs(val_int) in valid_counts):
            continue

        # Check if represents a whole EUR figure present in cents (e.g. "1000" for 1000 EUR -> 100,000 cents)
        if val_int is not None:
            cents_from_eur = val_int * 100
            if cents_from_eur in valid_cents or abs(cents_from_eur) in valid_cents:
                continue

        # Check if matches any valid percentage value (e.g. 18.5 without %)
        if any(abs(val_float - vp) < 0.05 for vp in valid_percents):
            continue

        # If it reached here, the number is not confirmed
        unconfirmed.append(raw)

    # Deduplicate unconfirmed while preserving discovery order
    unique_unconfirmed = list(dict.fromkeys(unconfirmed))
    return (len(unique_unconfirmed) == 0, unique_unconfirmed)
