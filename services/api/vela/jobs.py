"""Durable owner-scoped import outbox and conditional lease transitions."""
import base64
import binascii
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import time
from typing import Literal
from uuid import uuid4

from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.exc import IntegrityError
from .store import import_jobs, import_generations, private_originals, previews, Conflict
from .storage import StorageUnavailable
from .imports import MAX_BYTES, file_type


@dataclass(frozen=True)
class JobConfig:
    lease_seconds: int = 120
    heartbeat_seconds: int = 30
    max_attempts: int = 3
    backoff_seconds: int = 5

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in self.__dict__.values()) or self.heartbeat_seconds >= self.lease_seconds:
            raise ValueError('Positive operational job settings and heartbeat shorter than lease are required.')


class JobRecord(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ProcessingConsent(JobRecord):
    external_ai: bool = Field(strict=True)
    notice_version: Literal['import-processing-v1']


class EnqueueImport(JobRecord):
    filename: str = Field(min_length=1,max_length=180)
    content_type: str | None = Field(default=None,max_length=100)
    content_base64: str = Field(min_length=1,max_length=20971520)
    retention_consent: Literal[True]
    processing: ProcessingConsent

    @field_validator('retention_consent',mode='before')
    @classmethod
    def explicit_retention(cls,value):
        if value is not True:raise ValueError('Explicit retention consent must be true.')
        return value


class JobCommand(JobRecord):
    version: int = Field(strict=True,ge=0)


class JobView(JobRecord):
    job_id: str
    version: int
    status: Literal['uploading','queued','running','retry_wait','succeeded','failed','dead_letter','cancelled']
    stage: str
    attempts: int
    next_attempt_at: int | None
    result_preview_id: str | None
    error: str | None
    can_retry: bool
    can_cancel: bool
    status_url: str


class JobRepository:
    def __init__(self,store,storage,*,clock=None,config=None):
        self.store,self.storage=store,storage
        self.clock=clock or time.time
        self.config=config or JobConfig()

    @contextmanager
    def transaction(self):
        with self.store.lock,self.store.engine.begin() as conn:
            if conn.dialect.name=='sqlite': conn.exec_driver_sql('BEGIN IMMEDIATE')
            yield conn

    def row(self,conn,owner,job_id):
        row=conn.execute(select(import_jobs).where(import_jobs.c.owner==owner,import_jobs.c.job_id==job_id).with_for_update()).mappings().first()
        return dict(row) if row else None

    def source_live(self,conn,row,now):
        source=conn.execute(select(private_originals).where(private_originals.c.owner==row['owner'],private_originals.c.file_id==row['file_id']).with_for_update()).mappings().first()
        payload=json.loads(row['payload'])
        return bool(source and source['status']=='ready' and source['expires_at']>now and source['sha256']==payload['sha256'])

    def view(self,row,source_live=True):
        payload=json.loads(row['payload'])
        return JobView(job_id=row['job_id'],version=row['version'],status=row['status'],stage=payload.get('stage',row['status']),
            attempts=row['attempts'],next_attempt_at=row['next_attempt_at'] if row['status']=='retry_wait' else None,
            result_preview_id=payload.get('result_preview_id'),error=payload.get('error'),
            can_retry=row['status'] in ('failed','dead_letter') and source_live,
            can_cancel=row['status'] in ('uploading','queued','running','retry_wait'),status_url='/v1/jobs/'+row['job_id']).model_dump()

    def get(self,owner,job_id):
        with self.store.engine.connect() as conn:
            row=self.row(conn,owner,job_id)
            if row is None: raise FileNotFoundError()
            return self.view(row,self.source_live(conn,row,int(self.clock())))

    def replay(self,owner,key,body):
        fingerprint=hashlib.sha256(json.dumps(body.model_dump(),sort_keys=True).encode()).hexdigest()
        with self.store.engine.connect() as conn:
            row=conn.execute(select(import_jobs).where(import_jobs.c.owner==owner,import_jobs.c.key==key)).mappings().first()
            if row is None:raise Conflict('Import changed concurrently. Retry the same request.')
            if row['fingerprint']!=fingerprint:raise Conflict('This import retry key was used with different data.')
            return self.view(dict(row),self.source_live(conn,row,int(self.clock())))

    def enqueue(self,owner,key,body):
        try: data=base64.b64decode(body.content_base64,validate=True)
        except (binascii.Error,ValueError): raise ValueError('Choose a valid base64 statement.') from None
        if not data or len(data)>MAX_BYTES: raise ValueError('Statement must contain at most15MiB of bytes.')
        # Validate filename before any durable intent/provider side effect.
        if any(c in body.filename for c in ('..','/','\\','\x00')) or any(ord(c)<32 for c in body.filename):
            raise ValueError('Invalid statement filename.')
        file_type(body.filename,body.content_type,data)
        fingerprint=hashlib.sha256(json.dumps(body.model_dump(),sort_keys=True).encode()).hexdigest()
        now=int(self.clock())
        job_id,file_id=uuid4().hex,uuid4().hex
        payload={'filename':body.filename,'content_type':body.content_type,'processing':body.processing.model_dump(),
            'sha256':hashlib.sha256(data).hexdigest(),'parser_version':'import-parser-v1','stage':'uploading','commands':{}}
        with self.transaction() as conn:
            old=conn.execute(select(import_jobs).where(import_jobs.c.owner==owner,import_jobs.c.key==key)).mappings().first()
            if old:
                if old['fingerprint']!=fingerprint: raise Conflict('This import retry key was used with different data.')
                return self.view(dict(old),self.source_live(conn,old,now))
            generation=conn.execute(select(import_generations.c.generation).where(import_generations.c.owner==owner).with_for_update()).scalar_one_or_none()
            if generation is None:
                generation=uuid4().hex
                conn.execute(import_generations.insert().values(owner=owner,generation=generation))
            row=dict(owner=owner,job_id=job_id,key=key,fingerprint=fingerprint,generation=generation,file_id=file_id,
                version=0,status='uploading',attempts=0,next_attempt_at=now,lease_until=now+self.config.lease_seconds,
                lease_token='',created_at=now,updated_at=now,payload=json.dumps(payload))
            conn.execute(import_jobs.insert().values(**row))
        try:
            self.storage.save_file(owner,body.filename,data,retention_consent=True,_file_id=file_id)
        except StorageUnavailable:
            with self.transaction() as conn:
                current=self.row(conn,owner,job_id)
                if current and current['status']=='uploading':
                    payload.update(stage='failed',error='storage_unavailable')
                    conn.execute(update(import_jobs).where(import_jobs.c.owner==owner,import_jobs.c.job_id==job_id).values(status='failed',version=1,payload=json.dumps(payload)))
                    current={**current,'status':'failed','version':1,'payload':json.dumps(payload)}
                if current:return self.view(current,self.source_live(conn,current,int(self.clock())))
            raise Conflict('Import data was deleted during upload; no job was restored.') from None
        with self.transaction() as conn:
            current=self.row(conn,owner,job_id)
            live_generation=conn.execute(select(import_generations.c.generation).where(import_generations.c.owner==owner)).scalar_one_or_none()
            if current and current['status']=='uploading' and live_generation==generation and self.source_live(conn,current,int(self.clock())):
                payload['stage']='queued'
                conn.execute(update(import_jobs).where(import_jobs.c.owner==owner,import_jobs.c.job_id==job_id).values(status='queued',version=1,payload=json.dumps(payload),lease_until=0))
                row={**current,'status':'queued','version':1,'payload':json.dumps(payload)}
                return self.view(row)
        self.storage.erase_file(owner,file_id)
        raise Conflict('Import was cancelled or data was deleted during upload; no job was restored.')

    def claim(self):
        now=int(self.clock())
        with self.transaction() as conn:
            candidates=conn.execute(select(import_jobs).where(or_(
                and_(import_jobs.c.status.in_(('queued','retry_wait')),import_jobs.c.next_attempt_at<=now),
                and_(import_jobs.c.status.in_(('running','uploading')),import_jobs.c.lease_until<=now)))
                .order_by(import_jobs.c.created_at,import_jobs.c.job_id).with_for_update(skip_locked=True)).mappings().all()
            for candidate in candidates:
                row=dict(candidate)
                payload=json.loads(row['payload'])
                if not self.source_live(conn,row,now) or row['attempts']>=self.config.max_attempts:
                    payload.update(stage='failed',error='source_unavailable' if not self.source_live(conn,row,now) else 'attempts_exhausted')
                    conn.execute(update(import_jobs).where(import_jobs.c.owner==row['owner'],import_jobs.c.job_id==row['job_id']).values(
                        status='failed' if payload['error']=='source_unavailable' else 'dead_letter',version=row['version']+1,payload=json.dumps(payload)))
                    continue
                token=uuid4().hex
                payload.update(stage='reading',error=None)
                updates=dict(status='running',attempts=row['attempts']+1,version=row['version']+1,
                    lease_token=token,lease_until=now+self.config.lease_seconds,updated_at=now,payload=json.dumps(payload))
                changed=conn.execute(update(import_jobs).where(import_jobs.c.owner==row['owner'],import_jobs.c.job_id==row['job_id'],import_jobs.c.version==row['version']).values(**updates))
                if changed.rowcount==1:return {**row,**updates}
        return None

    def lease_live(self,conn,job,now,source=True):
        row=self.row(conn,job['owner'],job['job_id'])
        generation=conn.execute(select(import_generations.c.generation).where(import_generations.c.owner==job['owner']).with_for_update()).scalar_one_or_none()
        return bool(row and row['status']=='running' and row['lease_token']==job['lease_token'] and row['lease_until']>now
            and row['generation']==generation==job['generation'] and (not source or self.source_live(conn,row,now)))

    def heartbeat(self,job):
        now=int(self.clock())
        with self.transaction() as conn:
            if not self.lease_live(conn,job,now):return False
            conn.execute(update(import_jobs).where(import_jobs.c.owner==job['owner'],import_jobs.c.job_id==job['job_id']).values(lease_until=now+self.config.lease_seconds))
            return True

    def finish(self,job,preview):
        now=int(self.clock())
        with self.transaction() as conn:
            if not self.lease_live(conn,job,now):return False
            payload=json.loads(self.row(conn,job['owner'],job['job_id'])['payload'])
            preview_id='job-'+job['job_id']
            preview=preview.model_copy(update={'id':preview_id})
            conn.execute(previews.insert().values(owner=job['owner'],id=preview_id,payload=preview.model_dump_json()))
            payload.update(stage='complete',result_preview_id=preview_id,error=None)
            conn.execute(update(import_jobs).where(import_jobs.c.owner==job['owner'],import_jobs.c.job_id==job['job_id']).values(
                status='succeeded',version=job['version']+1,lease_token='',lease_until=0,updated_at=now,payload=json.dumps(payload)))
            return True

    def fail(self,job,*,permanent=False,code='processing_unavailable'):
        now=int(self.clock())
        with self.transaction() as conn:
            if not self.lease_live(conn,job,now,source=False):return False
            payload=json.loads(self.row(conn,job['owner'],job['job_id'])['payload'])
            status='failed' if permanent else 'dead_letter' if job['attempts']>=self.config.max_attempts else 'retry_wait'
            payload.update(stage=status,error=code)
            conn.execute(update(import_jobs).where(import_jobs.c.owner==job['owner'],import_jobs.c.job_id==job['job_id']).values(
                status=status,version=job['version']+1,lease_token='',lease_until=0,updated_at=now,
                next_attempt_at=now+self.config.backoff_seconds*2**(job['attempts']-1),payload=json.dumps(payload)))
            return True

    def command(self,owner,job_id,key,version,action):
        now=int(self.clock())
        fingerprint=hashlib.sha256(json.dumps({'version':version,'action':action},sort_keys=True).encode()).hexdigest()
        with self.transaction() as conn:
            row=self.row(conn,owner,job_id)
            if row is None:raise FileNotFoundError()
            payload=json.loads(row['payload'])
            old=payload['commands'].get(key)
            if old:
                if old['fingerprint']!=fingerprint:raise Conflict('This job retry key was used with different data.')
                return old['response']
            if row['version']!=version:raise Conflict('Job changed. Refresh before this command.')
            if action=='cancel' and row['status'] not in ('uploading','queued','running','retry_wait'):
                raise Conflict('Only an active import can be cancelled.')
            if action=='retry' and (row['status'] not in ('failed','dead_letter') or not self.source_live(conn,row,now)):
                raise Conflict('This import cannot be retried; choose a new file if necessary.')
            payload.update(stage='cancelled' if action=='cancel' else 'queued',error=None)
            updated={**row,'status':'cancelled' if action=='cancel' else 'queued','version':version+1,
                'attempts':row['attempts'] if action=='cancel' else 0,'next_attempt_at':now,'lease_until':0,'lease_token':'','payload':json.dumps(payload)}
            response=self.view(updated)
            payload['commands'][key]={'fingerprint':fingerprint,'response':response}
            conn.execute(update(import_jobs).where(import_jobs.c.owner==owner,import_jobs.c.job_id==job_id).values(
                **{k:updated[k] for k in ('status','version','attempts','next_attempt_at','lease_until','lease_token')},updated_at=now,payload=json.dumps(payload)))
            return response

    def cleanup(self):
        """Protect a live enqueue's pending source while provider put is in flight.

        Source IDs are allocated in the job intent BEFORE metadata/bytes and
        never attached to another job later. Therefore a missing live intent
        cannot race a new enqueue of this existing source ID.
        """
        now=int(self.clock())
        pending=0
        for source in self.store.list_originals():
            if source['status']=='ready' and source['expires_at']>now:continue
            with self.transaction() as conn:
                # Lock job before metadata, matching publication order. Re-read
                # metadata: the initial list can be stale after upload succeeds.
                jobs=conn.execute(select(import_jobs).where(import_jobs.c.owner==source['owner'],
                    import_jobs.c.file_id==source['file_id']).with_for_update()).mappings().all()
                if any(job['status']=='uploading' and job['lease_until']>now for job in jobs):continue
                current=conn.execute(select(private_originals).where(private_originals.c.owner==source['owner'],
                    private_originals.c.file_id==source['file_id']).with_for_update()).mappings().first()
                if current is None or (current['status']=='ready' and current['expires_at']>now):continue
                conn.execute(update(private_originals).where(private_originals.c.owner==source['owner'],
                    private_originals.c.file_id==source['file_id']).values(status='delete_pending'))
            pending+=not self.storage.erase_file(source['owner'],source['file_id'])
        return pending


def install_jobs(app,repository,owner,idempotency):
    @app.post('/v1/imports/jobs',response_model=JobView,status_code=202)
    def enqueue(body:EnqueueImport,who=Depends(owner),key=Depends(idempotency)):
        try:return repository.enqueue(who,key,body)
        except IntegrityError:return repository.replay(who,key,body)

    @app.get('/v1/jobs/{job_id}',response_model=JobView)
    def read(job_id:str,who=Depends(owner)):
        try:return repository.get(who,job_id)
        except FileNotFoundError:raise HTTPException(404,'Import job not found.') from None

    @app.post('/v1/jobs/{job_id}/retry',response_model=JobView)
    def retry(job_id:str,body:JobCommand,who=Depends(owner),key=Depends(idempotency)):
        try:return repository.command(who,job_id,key,body.version,'retry')
        except FileNotFoundError:raise HTTPException(404,'Import job not found.') from None

    @app.post('/v1/jobs/{job_id}/cancel',response_model=JobView)
    def cancel(job_id:str,body:JobCommand,who=Depends(owner),key=Depends(idempotency)):
        try:return repository.command(who,job_id,key,body.version,'cancel')
        except FileNotFoundError:raise HTTPException(404,'Import job not found.') from None
