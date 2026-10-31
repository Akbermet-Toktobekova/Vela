"""Immutable parsed evidence, explicit corrections and analytical-only application."""
from datetime import date
from datetime import date as CalendarDate
import hashlib
import json
from typing import Literal

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field


class ReconciliationRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')


class SourceRow(ReconciliationRecord):
    ordinal: int = Field(ge=1, strict=True)
    date: date
    amount: int = Field(ge=-1_000_000_000, le=1_000_000_000, strict=True)
    currency: str = Field(min_length=3, max_length=3)
    description: str = Field(min_length=1, max_length=200)
    category: str = 'other'
    category_method: str = 'legacy_unspecified'
    bank_reference: str | None = Field(default=None, max_length=200)
    booking_status: str | None = Field(default=None, max_length=60)


class Correction(ReconciliationRecord):
    version: int
    recorded_on: date
    reason: str
    fields: dict


class ReviewedRow(ReconciliationRecord):
    source_id: str
    original: SourceRow
    effective: SourceRow
    corrections: list[Correction] = Field(default_factory=list)
    decision_history: list[dict] = Field(default_factory=list)
    decision: Literal['new', 'link', 'unresolved'] = 'new'
    linked_id: str | None = None
    candidates: list[str] = Field(default_factory=list)
    applied_id: str | None = None


class ImportReview(ReconciliationRecord):
    id: str
    preview_id: str
    job_id: str | None = None
    file_id: str | None = None
    checksum: str
    account_id: str
    currency: str
    parser: str = 'legacy_unspecified'
    model: str | None = None
    parser_version: str = 'parsed-source-v1'
    version: int = 0
    applied: bool = False
    opening_balance: int | None = None
    closing_balance: int | None = None
    rows: list[ReviewedRow] = Field(default_factory=list)


class AnalyticalRow(ReconciliationRecord):
    id: str
    account_id: str
    value: SourceRow
    source_ids: list[str]


class ReconciliationState(ReconciliationRecord):
    reviews: list[ImportReview] = Field(default_factory=list)
    ledger: list[AnalyticalRow] = Field(default_factory=list)


class ReviewCreate(ReconciliationRecord):
    revision: int = Field(ge=0, strict=True)
    account_id: str = Field(min_length=1, max_length=80)


class ReviewCommand(ReconciliationRecord):
    revision: int = Field(ge=0, strict=True)
    review_version: int = Field(ge=0, strict=True)


class CorrectRow(ReviewCommand):
    date: CalendarDate | None = None
    amount: int | None = Field(default=None, ge=-1_000_000_000, le=1_000_000_000, strict=True)
    category: str | None = None
    reason: str = Field(min_length=1, max_length=200)


class ResolveRow(ReviewCommand):
    decision: Literal['new', 'link']
    linked_id: str | None = Field(default=None, max_length=80)


class ReviewView(ReconciliationRecord):
    revision: int
    review: ImportReview
    total_rows: int
    offset: int
    unresolved: int
    anchor_difference: int | None
    calculation_supported: bool


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()[:32]


def install_reconciliation(app, store, owner, idempotency, clock):
    from sqlalchemy import select
    from .domain import CATEGORIES, MAX_TRANSACTIONS, Transaction
    from .imports import ImportPreview
    from .store import Conflict, import_jobs, import_generations, previews

    def aggregate(state):
        if state.reconciliation is None:
            state.reconciliation = ReconciliationState()
        return state.reconciliation

    def find(state, review_id):
        result = next((r for r in (state.reconciliation.reviews if state.reconciliation else []) if r.id == review_id), None)
        if result is None:
            raise HTTPException(404, 'Review not found.')
        return result

    def view(state, review_id, offset=0, limit=100):
        review = find(state, review_id)
        difference = (review.opening_balance + sum(r.effective.amount for r in review.rows) - review.closing_balance
                      if review.opening_balance is not None and review.closing_balance is not None else None)
        projected = review.model_copy(deep=True)
        projected.rows = projected.rows[offset:offset+limit]
        return ReviewView(revision=state.revision, review=projected, total_rows=len(review.rows), offset=offset,
                          unresolved=sum(r.decision == 'unresolved' for r in review.rows), anchor_difference=difference,
                          calculation_supported=review.currency in ('EUR', 'HUF')).model_dump(mode='json')

    def guard_preview(who, preview_id, metadata=None):
        def guard(conn):
            if preview_id.startswith('job-'):
                job_id = preview_id[4:]
                row = conn.execute(select(import_jobs).where(import_jobs.c.owner == who, import_jobs.c.job_id == job_id).with_for_update()).mappings().first()
                generation = conn.execute(select(import_generations.c.generation).where(import_generations.c.owner == who).with_for_update()).scalar_one_or_none()
                if (not row or row['status'] != 'succeeded' or row['generation'] != generation
                        or json.loads(row['payload']).get('result_preview_id') != preview_id):
                    raise HTTPException(409, 'Source job is no longer current. Upload again.')
                if metadata is not None:
                    job_payload=json.loads(row['payload'])
                    metadata.update(file_id=row['file_id'],checksum=job_payload['sha256'],
                                    job_parser_version=job_payload.get('parser_version','unspecified'))
            payload = conn.execute(select(previews.c.payload).where(previews.c.owner == who, previews.c.id == preview_id).with_for_update()).scalar_one_or_none()
            if payload is None:
                raise HTTPException(404, 'Source preview not found.')
        return guard

    def mutate(who, key, body, review_id, kind, apply):
        preview_id = find(store.read(who), review_id).preview_id
        return store.mutate(who, key, body.revision, {'kind': kind, 'review_id': review_id, **body.model_dump(mode='json', exclude_unset=True)},
                            apply, lambda s: view(s, review_id), guard=guard_preview(who, preview_id))

    def current(state, review_id, version):
        review = find(state, review_id)
        if review.version != version or review.applied:
            raise Conflict('Review changed or was already applied. Refresh first.')
        return review

    def candidates(state, account_id, value):
        ledger = state.reconciliation.ledger if state.reconciliation else []
        exact = [r.id for r in ledger if r.account_id == account_id and r.value.currency == value.currency
                 and value.bank_reference and r.value.bank_reference == value.bank_reference]
        # Reused bank references with conflicting fields are ambiguous, never silently linked.
        proven = [r.id for r in ledger if r.id in exact and r.value.date == value.date and r.value.amount == value.amount]
        if len(exact) == len(proven) == 1:
            return 'link', proven[0], proven
        ambiguous = exact or [r.id for r in ledger if r.account_id == account_id and r.value.currency == value.currency
                              and (r.value.date, r.value.amount, r.value.description.lower()) == (value.date, value.amount, value.description.lower())]
        if value.currency == 'EUR':
            managed = {r.id for r in ledger}
            ambiguous += [t.id for t in state.transactions if t.id not in managed and
                          (t.date, t.amount, t.description.lower()) == (value.date, value.amount, value.description.lower())]
        return ('unresolved', None, list(dict.fromkeys(ambiguous))) if ambiguous else ('new', None, [])

    @app.post('/v2/imports/{preview_id}/review', response_model=ReviewView)
    def create(preview_id: str, body: ReviewCreate, who=Depends(owner), key=Depends(idempotency)):
        payload = store.get_preview(who, preview_id)
        if payload is None:
            raise HTTPException(404, 'Source preview not found.')
        imported = ImportPreview.model_validate_json(payload)
        source_metadata = {}
        review_id = 'review-'+digest(preview_id+'|'+body.account_id)
        def apply(state):
            account = next((a for a in state.personal.accounts if a.id == body.account_id), None)
            if account is None or account.currency != imported.currency:
                raise ValueError('Choose an owned account with the statement currency.')
            data = aggregate(state)
            if any(r.id == review_id for r in data.reviews):
                raise Conflict('This source already has a review. Resume it.')
            checksum = imported.source_checksum or 'legacy-preview:'+preview_id
            if source_metadata and source_metadata['checksum'] != checksum:
                raise ValueError('Parsed source checksum differs from its job.')
            source_rows = imported.source_rows or [SourceRow(ordinal=i+1, date=t.date, amount=t.amount,
                currency=imported.currency, description=t.description, category=t.category) for i,t in enumerate(imported.transactions)]
            if len({r.ordinal for r in source_rows}) != len(source_rows):
                raise ValueError('Source row ordinals must be unique.')
            review = ImportReview(id=review_id, preview_id=preview_id, account_id=account.id, currency=imported.currency,
                checksum=checksum, job_id=preview_id[4:] if preview_id.startswith('job-') else None,
                file_id=source_metadata.get('file_id'),
                parser=imported.parser,model=imported.model,
                parser_version=imported.source_method_version+'|'+source_metadata.get('job_parser_version','sync'),
                opening_balance=imported.opening_balance, closing_balance=imported.closing_balance)
            # Source row identity is checksum/account/ordinal, preserving equal purchases.
            known = {sid: row for row in data.ledger for sid in row.source_ids}
            for original in source_rows:
                if original.currency != imported.currency:
                    raise ValueError('Mixed-currency source rows require separate review.')
                source_id = 'src-'+digest(checksum+'|'+account.id+'|'+review.parser_version+'|'+str(original.ordinal))
                decision, linked_id, options = candidates(state, account.id, original)
                if source_id in known:
                    decision, linked_id, options = 'link', known[source_id].id, [known[source_id].id]
                elif original.bank_reference:
                    prior=next((r for r in review.rows if r.original.bank_reference==original.bank_reference),None)
                    if prior:
                        decision,linked_id='unresolved',None
                        options=([prior.source_id] if (prior.effective.date,prior.effective.amount)==(original.date,original.amount) else [])
                review.rows.append(ReviewedRow(source_id=source_id, original=original.model_copy(deep=True),
                    effective=(known[source_id].value.model_copy(deep=True) if source_id in known else original.model_copy(deep=True)),
                    decision=decision, linked_id=linked_id, candidates=options))
            data.reviews.append(review)
        return store.mutate(who, key, body.revision, {'kind':'reconciliation_review','preview_id':preview_id,**body.model_dump()},
                            apply, lambda s:view(s,review_id), guard=guard_preview(who,preview_id,source_metadata))

    @app.get('/v2/reviews/{review_id}', response_model=ReviewView)
    def read(review_id: str, offset: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200), who=Depends(owner)):
        return view(store.read(who), review_id, offset, limit)

    @app.put('/v2/reviews/{review_id}/rows/{source_id}', response_model=ReviewView)
    def correct(review_id: str, source_id: str, body: CorrectRow, who=Depends(owner), key=Depends(idempotency)):
        def apply(state):
            review = current(state,review_id,body.review_version)
            row = next((r for r in review.rows if r.source_id == source_id), None)
            if row is None:
                raise HTTPException(404,'Source row not found.')
            if any(row.source_id in item.source_ids for item in aggregate(state).ledger):
                raise ValueError('This exact source row was already applied. Resume its existing provenance.')
            changes = {k:getattr(body,k) for k in ('date','amount','category') if k in body.model_fields_set}
            if not changes or any(v is None for v in changes.values()) or not body.reason.strip():
                raise ValueError('Provide a correction and reason, without null money/date/category.')
            if changes.get('category',row.effective.category) not in CATEGORIES:
                raise ValueError('Unsupported analytical category.')
            if 'date' in changes and changes['date'] > clock():
                raise ValueError('A statement correction date cannot be in the future.')
            row.effective = SourceRow.model_validate({**row.effective.model_dump(),**changes,
                **({'category_method':'manual_correction'} if 'category' in changes else {})})
            row.corrections.append(Correction(version=review.version+1, recorded_on=clock(),reason=body.reason,
                                               fields={k:(v.isoformat() if isinstance(v,date) else v) for k,v in changes.items()}))
            row.decision,row.linked_id,row.candidates=candidates(state,review.account_id,row.effective)
            # A field correction is not an explicit duplicate decision. Keep a
            # repeated in-file bank reference unresolved just as at review creation.
            prior=next((r for r in review.rows[:review.rows.index(row)]
                        if row.original.bank_reference and r.original.bank_reference==row.original.bank_reference),None)
            if prior is not None:
                row.decision,row.linked_id='unresolved',None
                row.candidates=([prior.source_id] if (prior.effective.date,prior.effective.amount)==
                                (row.effective.date,row.effective.amount) else [])
            # A sibling's previous duplicate choice depended on these effective
            # fields. Preserve that history, but require an explicit choice again.
            for dependent in review.rows:
                if dependent.decision=='link' and dependent.linked_id==row.source_id:
                    dependent.decision,dependent.linked_id='unresolved',None
                    dependent.candidates=([row.source_id] if (dependent.effective.date,dependent.effective.amount)==
                                          (row.effective.date,row.effective.amount) else [])
                    dependent.decision_history.append({'version':review.version+1,'recorded_on':clock().isoformat(),
                        'decision':'unresolved','linked_id':None,'previous_linked_id':row.source_id,
                        'reason':'linked_source_corrected'})
            review.version += 1
        return mutate(who,key,body,review_id,'reconciliation_correct:'+source_id,apply)

    @app.post('/v2/reviews/{review_id}/rows/{source_id}/resolve', response_model=ReviewView)
    def resolve(review_id: str, source_id: str, body: ResolveRow, who=Depends(owner), key=Depends(idempotency)):
        def apply(state):
            review=current(state,review_id,body.review_version)
            row=next((r for r in review.rows if r.source_id==source_id),None)
            if row is None:raise HTTPException(404,'Source row not found.')
            known=next((item for item in aggregate(state).ledger if row.source_id in item.source_ids),None)
            if known is not None and (body.decision!='link' or body.linked_id!=known.id):
                raise ValueError('An exact applied source cannot become a distinct purchase.')
            if body.decision=='link':
                if not body.linked_id or body.linked_id not in row.candidates:
                    raise ValueError('Choose an offered owned analytical row.')
            elif body.linked_id is not None:
                raise ValueError('A distinct purchase cannot link an existing row.')
            row.decision,row.linked_id=body.decision,body.linked_id
            row.decision_history.append({'version':review.version+1,'recorded_on':clock().isoformat(),
                                         'decision':body.decision,'linked_id':body.linked_id})
            review.version+=1
        return mutate(who,key,body,review_id,'reconciliation_resolve:'+source_id,apply)

    @app.post('/v2/reviews/{review_id}/apply', response_model=ReviewView)
    def apply_review(review_id: str, body: ReviewCommand, who=Depends(owner), key=Depends(idempotency)):
        def apply(state):
            review=current(state,review_id,body.review_version)
            if review.currency not in ('EUR','HUF') or any(r.decision=='unresolved' for r in review.rows):
                raise ValueError('Resolve ambiguous rows and supported currency before applying.')
            data=aggregate(state)
            for row in review.rows:
                known=next((item for item in data.ledger if row.source_id in item.source_ids),None)
                if known is not None:
                    if known.value != row.effective:
                        raise Conflict('This source was already applied with different reviewed fields.')
                    row.decision,row.linked_id='link',known.id
                linked_id=row.linked_id
                if row.decision=='link' and linked_id and linked_id.startswith('src-'):
                    prior=next((r for r in review.rows if r.source_id==linked_id),None)
                    if prior is None or (prior.effective.date,prior.effective.amount,prior.effective.currency)!=(
                            row.effective.date,row.effective.amount,row.effective.currency):
                        raise Conflict('Linked source fields changed. Review the duplicate decision again.')
                    linked_id=prior.applied_id if prior is not None else None
                target=next((r for r in data.ledger if r.id==linked_id),None) if row.decision=='link' else None
                if row.decision=='link' and target is None:
                    legacy=next((t for t in state.transactions if t.id==linked_id),None)
                    if legacy is None or review.currency!='EUR':raise ValueError('Linked analytical row no longer exists.')
                    target=AnalyticalRow(id=legacy.id,account_id=review.account_id,
                        value=SourceRow(ordinal=row.original.ordinal,date=legacy.date,amount=legacy.amount,currency='EUR',
                                        description=legacy.description,category=legacy.category),source_ids=[])
                    data.ledger.append(target)
                if target is not None:
                    if target.account_id!=review.account_id or target.value.currency!=review.currency:
                        raise ValueError('Linked row account or currency changed.')
                    if row.source_id not in target.source_ids:target.source_ids.append(row.source_id)
                else:
                    target=AnalyticalRow(id='rec-'+digest(review.id+'|'+row.source_id),account_id=review.account_id,
                                         value=row.effective.model_copy(deep=True),source_ids=[row.source_id])
                    data.ledger.append(target)
                row.applied_id=target.id
                if review.currency=='EUR' and not any(t.id==target.id for t in state.transactions):
                    state.transactions.append(Transaction(id=target.id,date=target.value.date,amount=target.value.amount,
                        description=target.value.description,category=target.value.category,source='import:reconciled'))
            if len(state.transactions)>MAX_TRANSACTIONS:raise ValueError('Analytical history limit reached; no entries removed.')
            state.transactions.sort(key=lambda t:(t.date,t.id),reverse=True)
            review.applied=True
            review.version+=1
        return mutate(who,key,body,review_id,'reconciliation_apply',apply)
