"""Read-only ECB display valuations; never affordability or confirmed money."""
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import json
from threading import RLock
from typing import Callable, Iterable

import httpx


SUPPORTED = frozenset({'EUR', 'HUF'})
MAX_MINOR = 9_007_199_254_740_991
SOURCE = 'ECB via Frankfurter v2'


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def currency(value: str) -> str:
    if value not in SUPPORTED:
        raise ValueError('Only EUR/HUF display valuation is supported.')
    return value


@dataclass(frozen=True)
class Quote:
    base: str
    quote: str
    rate: Decimal
    rate_date: date
    requested_on: date
    source: str = SOURCE


@dataclass(frozen=True)
class Amount:
    minor: int | None
    currency: str

    def __post_init__(self):
        currency(self.currency)
        if self.minor is not None and (type(self.minor) is not int or abs(self.minor) > MAX_MINOR):
            raise ValueError('Amount must be integer minor units within the safe integer range, or unknown.')


@dataclass(frozen=True)
class ValuedAmount:
    original: Amount
    converted_minor: Decimal | None
    quote: Quote | None
    unavailable: str | None = None


@dataclass(frozen=True)
class Valuation:
    currency: str
    lines: tuple[ValuedAmount, ...]
    # None is incomplete, not zero and not a partial sum presented as a total.
    exact_total_minor: Decimal | None
    total_minor: int | None
    complete: bool
    estimated: bool


class ECBRates:
    """Bounded process cache of public quotes; no account data leaves this class.

    Latest queries are keyed by UTC/caller clock day, historical by requested
    date. Historical API carry-forward is accepted only on/before that date.
    No missing/error result is cached; an outage cannot become a zero rate.
    """
    def __init__(self, client: httpx.Client, *, today: Callable[[], date] = utc_today,
                 cache_size: int = 256):
        if type(cache_size) is not int or cache_size < 1:
            raise ValueError('Positive cache size required.')
        self.client, self.today, self.cache_size = client, today, cache_size
        self._cache: OrderedDict[tuple, Quote] = OrderedDict()
        self._lock = RLock()

    def get(self, base: str, target: str, *, on: date | None = None) -> Quote | None:
        currency(base)
        currency(target)
        current = self.today()
        requested = on or current
        if type(requested) is not date or requested > current:
            raise ValueError('FX date must be today or an earlier date.')
        if base == target:
            return Quote(base, target, Decimal(1), requested, requested, 'identity')
        key = (base, target, requested, on is None)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
        params = {'date': requested.isoformat()} if on is not None else {}
        try:
            response = self.client.get(
                f'https://api.frankfurter.dev/v2/providers/ecb/rate/{base.lower()}/{target.lower()}',
                params=params, timeout=5.0, follow_redirects=False)
            response.raise_for_status()
            # Decode numbers directly into Decimal, never through binary float.
            payload = json.loads(response.content, parse_float=Decimal, parse_int=Decimal)
            if not isinstance(payload, dict) or payload.get('base') != base or payload.get('quote') != target:
                return None
            rate = payload.get('rate')
            published = date.fromisoformat(payload['date'])
            if (not isinstance(rate, Decimal) or not rate.is_finite() or rate <= 0
                    or len(rate.as_tuple().digits) > 40 or abs(rate.as_tuple().exponent) > 40
                    or published > requested):
                return None
            result = Quote(base, target, rate, published, requested)
        except (httpx.HTTPError, ValueError, TypeError, KeyError, InvalidOperation, OverflowError):
            return None
        with self._lock:
            self._cache[key] = result
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
        return result


def value_amounts(amounts: Iterable[Amount], rates: ECBRates, *, target: str = 'EUR',
                  on: date | None = None) -> Valuation:
    """Preserve originals; round the exact total once at output minor unit.

    Both currencies use two minor digits. Owner approved nearest/HALF_UP on
    2026-10-29: EUR1.005 becomes EUR1.01; negative ties round away from zero.
    Intermediate converted lines deliberately remain unrounded Decimal values.
    """
    currency(target)
    lines = []
    for amount in amounts:
        if not isinstance(amount, Amount):
            raise TypeError('Explicit Amount records required.')
        if amount.minor is None:
            lines.append(ValuedAmount(amount, None, None, 'unknown_amount'))
            continue
        quote = rates.get(amount.currency, target, on=on)
        if quote is None:
            lines.append(ValuedAmount(amount, None, None, 'missing_rate'))
            continue
        with localcontext() as ctx:
            ctx.prec = 100
            converted = Decimal(amount.minor) * quote.rate
        lines.append(ValuedAmount(amount, converted, quote))
    complete = all(line.converted_minor is not None for line in lines)
    with localcontext() as ctx:
        # Input bounds/rate precision are explicit; accommodate aggregation too.
        ctx.prec = 100 + len(str(len(lines)))
        total = sum((line.converted_minor for line in lines), Decimal(0)) if complete else None
        rounded = int(total.quantize(Decimal(1), rounding=ROUND_HALF_UP)) if total is not None else None
    if rounded is not None and abs(rounded) > MAX_MINOR:
        raise ValueError('Converted total exceeds the safe integer range.')
    return Valuation(target, tuple(lines), total, rounded, complete,
                     any(line.original.currency != target for line in lines))
