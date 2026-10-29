"""Deterministic, read-only suggestions over stored analytical rows, not money commands."""
from collections import defaultdict
from datetime import date
import hashlib
import re
from typing import Literal

from pydantic import Field
from .domain import Record, State
from .imports import _normalize


class Observation(Record):
    id: str
    kind: Literal['recurring_payment', 'price_change', 'income_series', 'category_totals', 'refund_link', 'own_transfer_evidence']
    label: str
    status: Literal['suggested'] = 'suggested'
    method_version: str = 'recorded-evidence-v1'
    evidence_ids: list[str]
    periods: list[str]
    amounts: list[int]
    difference: int | None = None
    note: str


class ObservationsView(Record):
    revision: int
    currency: Literal['EUR'] = 'EUR'
    period_start: date | None
    period_end: date | None
    transaction_count: int
    observations: list[Observation] = Field(default_factory=list)


def analyse(state: State) -> ObservationsView:
    rows = sorted(state.transactions, key=lambda t: (t.date, t.id))
    results = []

    def add(kind, key, label, evidence, periods, amounts, note, difference=None):
        results.append(Observation(id=hashlib.sha256(f'{kind}|{key}'.encode()).hexdigest()[:20],
                                  kind=kind, label=label, evidence_ids=[t.id for t in evidence],
                                  periods=periods, amounts=amounts, note=note, difference=difference))

    groups = defaultdict(list)
    for t in rows:
        if t.category not in ('transfers', 'refunds'):
            # References remain in stored evidence; they do not define the merchant.
            groups[(_normalize(t.description.split(' · ')[0]), t.amount > 0)].append(t)
    for (key, incoming), items in sorted(groups.items()):
        months = [t.date.strftime('%Y-%m') for t in items]
        # One payment per observed month avoids calling frequent purchases a subscription.
        if len(set(months)) < 2 or len(set(months)) != len(items):
            continue
        amounts = [abs(t.amount) for t in items]
        label = items[-1].description.split(' · ')[0]
        if incoming:
            add('income_series', key, label, items, months, amounts,
                'Observed credits only. This does not confirm future income.')
        elif len({t.date.day for t in items}) == 1:
            add('recurring_payment', key, label, items, months, amounts,
                'Possible recurring payment in recorded months. Confirm its purpose; no bill was created.')
            if len(set(amounts)) > 1:
                add('price_change', key, label, items, months, amounts,
                    'Recorded charge amounts changed. This alone does not establish a contractual price increase.',
                    difference=amounts[-1]-amounts[-2])

    by_category = defaultdict(list)
    for t in rows:
        if t.amount < 0 and t.category != 'transfers':
            by_category[t.category].append(t)
    for category, items in sorted(by_category.items()):
        totals = defaultdict(int)
        for t in items:
            totals[t.date.strftime('%Y-%m')] -= t.amount
        periods = sorted(totals)
        if len(periods) > 1:
            add('category_totals', category, f'Recorded {category} debits', items, periods,
                [totals[m] for m in periods], 'Recorded rows only; monthly coverage may be partial. Refunds are shown separately.')

    refs = defaultdict(list)
    for t in rows:
        for ref in set(re.findall(r'\bREF-[A-Z0-9]+(?:-[A-Z0-9]+)*\b', t.description.upper())):
            refs[ref].append(t)
    for ref, items in sorted(refs.items()):
        purchases = [t for t in items if t.amount < 0 and t.category != 'transfers']
        refunds = [t for t in items if t.amount > 0 and t.category == 'refunds']
        if len(purchases) == 1 and refunds and sum(t.amount for t in refunds) <= -purchases[0].amount and all(t.date >= purchases[0].date for t in refunds):
            evidence = purchases+refunds
            add('refund_link', ref, f'Possible refund match {ref}', evidence,
                [str(t.date) for t in evidence], [t.amount for t in evidence],
                'Matching explicit reference and amounts; suggested association, not a confirmed reconciliation.')
    transfers = [t for t in rows if t.category == 'transfers']
    if transfers:
        add('own_transfer_evidence', 'labelled-transfers', 'Entries labelled as transfers', transfers,
            [str(t.date) for t in transfers], [t.amount for t in transfers],
            'Category based on source descriptions. Account ownership has not been independently confirmed.')
    return ObservationsView(revision=state.revision, period_start=rows[0].date if rows else None,
                            period_end=rows[-1].date if rows else None, transaction_count=len(rows), observations=results)
