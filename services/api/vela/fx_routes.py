"""Authenticated, read-only account display valuations; no planning effects."""
from datetime import date
from typing import Literal

from fastapi import Depends, HTTPException, Query
import httpx
from pydantic import Field

from .domain import Record
from .fx import Amount, ECBRates, MAX_MINOR, value_amounts


class OriginalAmount(Record):
    amount_minor: int | None
    currency: Literal['EUR', 'HUF']


class QuoteView(Record):
    base: Literal['EUR', 'HUF']
    quote: Literal['EUR', 'HUF']
    rate: str
    rate_date: date
    requested_on: date
    source: str


class AccountValuationLine(Record):
    account_id: str
    original: OriginalAmount
    converted_minor_exact: str | None
    unavailable: Literal['unknown_amount', 'missing_rate'] | None
    quote: QuoteView | None


class AccountsValuationView(Record):
    revision: int
    target_currency: Literal['EUR'] = 'EUR'
    requested_on: date
    rate_mode: Literal['latest', 'historical_reference']
    complete: bool
    estimated: bool
    total_minor: int | None = Field(ge=-MAX_MINOR, le=MAX_MINOR)
    lines: list[AccountValuationLine]
    balance_basis: Literal['current_confirmed_balances'] = 'current_confirmed_balances'


class _ClosedAfterRequestClient:
    """A cache miss owns one buffered HTTP request and closes its connection.

    App factories/tests need no long-lived client or additional shutdown hook.
    The public rate cache survives client closure; httpx.get eagerly reads bytes.
    """
    def get(self, url, **kwargs):
        with httpx.Client() as client:
            return client.get(url, **kwargs)


def install_fx(app, store, owner, clock, *, rates=None):
    public_rates = rates if rates is not None else ECBRates(_ClosedAfterRequestClient(), today=clock)

    @app.get('/v2/valuations/accounts', response_model=AccountsValuationView)
    def accounts_valuation(on: date | None = Query(default=None), who=Depends(owner)):
        requested = on or clock()
        if requested > clock():
            raise HTTPException(422, 'FX date must be today or an earlier date.')
        # One owner-scoped revision. Historical reference changes rates only,
        # never claims a reconstruction of historical account balances.
        state = store.read(who)
        accounts = state.personal.accounts
        try:
            valued = value_amounts([Amount(account.balance, account.currency) for account in accounts],
                                  public_rates, on=on)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        lines = []
        for account, line in zip(accounts, valued.lines):
            q = line.quote
            lines.append(AccountValuationLine(
                account_id=account.id,
                original=OriginalAmount(amount_minor=line.original.minor, currency=line.original.currency),
                converted_minor_exact=str(line.converted_minor) if line.converted_minor is not None else None,
                unavailable=line.unavailable,
                quote=QuoteView(base=q.base, quote=q.quote, rate=str(q.rate), rate_date=q.rate_date,
                                requested_on=q.requested_on, source=q.source) if q else None))
        return AccountsValuationView(revision=state.revision, requested_on=requested,
                                     rate_mode='latest' if on is None else 'historical_reference',
                                     complete=valued.complete, estimated=valued.estimated,
                                     total_minor=valued.total_minor, lines=lines)
