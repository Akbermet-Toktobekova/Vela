import asyncio
from datetime import date
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
import unittest
from unittest.mock import patch

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import select, delete

from vela.domain import State, fixture
from vela.imports import ImportPreview, build_preview
from vela.personal import Account, ReceivedIncome
from vela.reconciliation import SourceRow, ImportReview, ReconciliationState, install_reconciliation
from vela.store import Store, Conflict, states, receipts, import_jobs, import_generations


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.url=f'sqlite:///{Path(self.temp.name)/"synthetic-reconciliation.db"}'
        self.day=date(2026,10,29)
        self.make_app()
        for who in ('A','B'):
            def seed(s):
                s.personal.accounts=[Account(id='eur',name='Synthetic',currency='EUR',balance=100000,confirmed_on=self.day),
                                     Account(id='huf',name='Synthetic HUF',currency='HUF',balance=None)]
                s.personal.incomes=[ReceivedIncome(id='manual-income',account_id='eur',amount=5000,received_on=self.day,effect='included')]
            self.store.mutate(who,'seed-account',0,{'kind':'seed'},seed,lambda s:{'revision':s.revision})

    def make_app(self):
        self.store=Store(self.url)
        app=FastAPI()
        def owner(authorization:Annotated[str|None,Header()]=None):
            if authorization not in ('Bearer A','Bearer B'):raise HTTPException(401,'Synthetic credentials required.')
            return authorization[-1]
        def key(idempotency_key:Annotated[str,Header(min_length=8)]):return idempotency_key
        @app.exception_handler(ValueError)
        async def invalid(request,exc):return JSONResponse({'detail':str(exc)},status_code=422)
        @app.exception_handler(Conflict)
        async def conflict(request,exc):return JSONResponse({'detail':str(exc)},status_code=409)
        install_reconciliation(app,self.store,owner,key,lambda:self.day)
        self.client=TestClient(app)

    def tearDown(self):
        self.client.close();self.store.engine.dispose();self.temp.cleanup()

    def preview(self,id='preview-1',who='A',currency='EUR',checksum='a'*64,rows=None):
        if rows is None:
            rows=[(5000,'Salary','income','income-ref'),(-2000,'Shop','groceries',None),
                  (-2000,'Shop','groceries',None),(-3000,'Own transfer','transfers','transfer-ref')]
        source=[SourceRow(ordinal=i+1,date=self.day,amount=a,currency=currency,description=d,category=c,bank_reference=r)
                for i,(a,d,c,r) in enumerate(rows)]
        result=ImportPreview(id=id,filename='synthetic.csv',file_type='csv',parser='local',currency=currency,
            opening_balance=10000,closing_balance=8000,source_checksum=checksum,source_rows=source)
        self.store.save_preview(who,id,result.model_dump_json())
        return result

    def call(self,path,body=None,who='A',key='reconciliation-command',method='POST'):
        return self.client.request(method,path,headers={'Authorization':'Bearer '+who,'Idempotency-Key':key},json=body)

    def create(self,id='preview-1',who='A',account='eur',key='create-review-command'):
        response=self.call('/v2/imports/'+id+'/review',{'revision':self.store.read(who).revision,'account_id':account},who,key)
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def apply(self,data,key='apply-review-command',who='A'):
        return self.call('/v2/reviews/'+data['review']['id']+'/apply',
            {'revision':data['revision'],'review_version':data['review']['version']},who,key)

    def rows(self,who='A'):
        with self.store.engine.connect() as conn:
            return (conn.execute(select(states).where(states.c.owner==who)).fetchall(),
                    conn.execute(select(receipts).where(receipts.c.owner==who)).fetchall())

    def test_equal_purchase_multiplicity_fixed_anchor_and_money_oracle(self):
        self.preview()
        financial=self.store.read('A').personal.model_dump()
        data=self.create()
        self.assertEqual(data['anchor_difference'],0)
        self.assertEqual(data['unresolved'],0)
        result=self.apply(data)
        self.assertEqual(result.status_code,200,result.text)
        state=self.store.read('A')
        self.assertEqual(len(state.transactions),4)
        self.assertEqual(sum(t.amount for t in state.transactions),-2000)
        self.assertEqual(sum(-t.amount for t in state.transactions if t.amount<0 and t.category!='transfers'),4000)
        self.assertEqual(len({t.id for t in state.transactions}),4)
        self.assertEqual(state.personal.model_dump(),financial)
        self.assertEqual(state.personal.accounts[0].balance,100000)
        self.assertEqual(len(state.personal.incomes),1)
        self.assertIsNone(state.snapshot)
        self.assertEqual([r.original.booking_status for r in state.reconciliation.reviews[0].rows],[None]*4)

    def test_same_source_different_joblinks_once_and_exact_retry(self):
        self.preview();data=self.create();first=self.apply(data)
        before=self.rows()
        self.assertEqual(self.apply(data).json(),first.json())
        self.assertEqual(self.rows(),before)
        self.preview('preview-2')
        second=self.create('preview-2',key='second-source-review')
        self.assertTrue(all(r['decision']=='link' for r in second['review']['rows']))
        source_id=second['review']['rows'][1]['source_id']
        before=self.rows()
        self.assertEqual(self.call(f"/v2/reviews/{second['review']['id']}/rows/{source_id}/resolve",
            {'revision':second['revision'],'review_version':0,'decision':'new'},key='cannot-duplicate-exact').status_code,422)
        self.assertEqual(self.call(f"/v2/reviews/{second['review']['id']}/rows/{source_id}",
            {'revision':second['revision'],'review_version':0,'amount':-2500,'reason':'already applied'},
            key='cannot-edit-exact-source',method='PUT').status_code,422)
        self.assertEqual(self.rows(),before)
        self.assertEqual(self.apply(second,'second-source-apply').status_code,200)
        self.assertEqual(len(self.store.read('A').transactions),4)

    def test_overlap_reference_auto_and_tuple_only_explicit_distinct(self):
        self.preview();self.apply(self.create())
        self.preview('overlap',checksum='b'*64,rows=[(5000,'Salary','income','income-ref'),(-2000,'Shop','groceries',None)])
        data=self.create('overlap',key='overlap-review')
        self.assertEqual([r['decision'] for r in data['review']['rows']],['link','unresolved'])
        before=self.rows()
        self.assertEqual(self.apply(data,'unresolved-apply').status_code,422)
        self.assertEqual(self.rows(),before)
        row=data['review']['rows'][1]
        resolved=self.call(f"/v2/reviews/{data['review']['id']}/rows/{row['source_id']}/resolve",
            {'revision':data['revision'],'review_version':0,'decision':'new'},key='explicit-distinct').json()
        self.assertEqual(self.apply(resolved,'resolved-apply').status_code,200)
        state=self.store.read('A')
        self.assertEqual(len(state.transactions),5)
        self.assertEqual(sum(-t.amount for t in state.transactions if t.category=='groceries'),6000)
        self.assertEqual(len(state.reconciliation.reviews[1].rows[1].decision_history),1)

    def test_correction_history_original_and_difference_retained(self):
        self.preview();data=self.create()
        row=data['review']['rows'][2]
        corrected=self.call(f"/v2/reviews/{data['review']['id']}/rows/{row['source_id']}",
            {'revision':data['revision'],'review_version':0,'amount':-2500,'reason':'Statement correction'},
            key='correct-source-row',method='PUT')
        self.assertEqual(corrected.status_code,200,corrected.text)
        data=corrected.json()
        self.assertEqual(data['anchor_difference'],-500)
        self.assertEqual(data['review']['rows'][2]['original']['amount'],-2000)
        self.assertEqual(data['review']['rows'][2]['corrections'][0]['fields'],{'amount':-2500})
        self.assertEqual(self.apply(data).status_code,200)
        state=self.store.read('A')
        self.assertEqual(sum(-t.amount for t in state.transactions if t.category=='groceries'),4500)
        self.assertEqual(state.personal.accounts[0].balance,100000)

    def test_owner_account_currency_validation_and_huf_not_eur_projection(self):
        self.preview();data=self.create()
        self.assertEqual(self.call('/v2/reviews/'+data['review']['id'],who='B',method='GET').status_code,404)
        self.assertEqual(self.call('/v2/imports/preview-1/review',{'revision':1,'account_id':'eur'},who='B').status_code,404)
        before=self.rows()
        self.preview('wrong-account')
        self.assertEqual(self.call('/v2/imports/wrong-account/review',{'revision':2,'account_id':'foreign'}).status_code,422)
        self.assertEqual(self.rows(),before)
        self.preview('huf-source',currency='HUF',rows=[(-400000,'HUF shop','shopping',None)])
        huf=self.create('huf-source',account='huf',key='huf-review')
        self.assertEqual(self.apply(huf,'huf-apply').status_code,200)
        state=self.store.read('A')
        self.assertEqual(state.transactions,[])
        self.assertEqual(state.reconciliation.ledger[0].value.currency,'HUF')
        self.assertIsNone(state.personal.accounts[1].balance)

    def test_changed_body_stale_version_and_null_precision_rollback(self):
        self.preview();data=self.create()
        before=self.rows()
        self.assertEqual(self.call('/v2/imports/preview-1/review',{'revision':1,'account_id':'huf'},key='create-review-command').status_code,409)
        path=f"/v2/reviews/{data['review']['id']}/rows/{data['review']['rows'][0]['source_id']}"
        for amount in (None,True,1.5):
            self.assertEqual(self.call(path,{'revision':2,'review_version':0,'amount':amount,'reason':'x'},method='PUT').status_code,422)
        self.assertEqual(self.call(path,{'revision':2,'review_version':9,'amount':7,'reason':'x'},method='PUT').status_code,409)
        self.assertEqual(self.rows(),before)

    def test_restart_readonly_pagination_and_deleted_preview_guard_before_receipt(self):
        self.preview();data=self.create();self.apply(data)
        before=self.rows()
        self.client.close();self.store.engine.dispose();self.make_app()
        page=self.call('/v2/reviews/'+data['review']['id']+'?offset=1&limit=2',method='GET').json()
        self.assertEqual((page['total_rows'],page['offset'],len(page['review']['rows'])),(4,1,2))
        self.assertEqual(self.rows(),before)
        self.store.delete_preview('A','preview-1')
        self.assertEqual(self.apply(data).status_code,404)
        self.assertEqual(self.rows(),before)

    def test_deleted_job_guard_before_cached_retry_and_raw_expiry_retains_facts(self):
        self.preview('job-sourcejob')
        payload={'result_preview_id':'job-sourcejob','sha256':'a'*64}
        with self.store.engine.begin() as conn:
            conn.execute(import_generations.insert().values(owner='A',generation='generation'))
            conn.execute(import_jobs.insert().values(owner='A',job_id='sourcejob',key='job-key',fingerprint='f',generation='generation',file_id='expired-original',
                version=1,status='succeeded',attempts=1,next_attempt_at=0,lease_until=0,lease_token='',created_at=0,updated_at=0,payload=json.dumps(payload)))
        data=self.create('job-sourcejob')
        self.assertEqual(data['review']['file_id'],'expired-original')
        self.assertEqual(self.apply(data).status_code,200)
        before=self.rows()
        with self.store.engine.begin() as conn:
            conn.execute(delete(import_jobs).where(import_jobs.c.owner=='A'))
        self.assertEqual(self.apply(data).status_code,409)
        self.assertEqual(self.rows(),before)
        self.assertEqual(self.call('/v2/reviews/'+data['review']['id'],method='GET').status_code,200)

    def test_parser_source_ordinals_reference_and_checksum_before_dedupe(self):
        raw=b'date,description,amount,currency,reference,status\n2026-10-28,Shop,-20.00,EUR,,\n2026-10-28,Shop,-20.00,EUR,,\n2026-10-28,Salary,50.00,EUR,bank-123,booked\n'
        with patch('vela.imports.enabled',return_value=False):
            parsed=asyncio.run(build_preview(raw,'synthetic.csv','text/csv',None,self.day,'parsed',external_ai_allowed=False))
        self.assertEqual(parsed.source_checksum,hashlib.sha256(raw).hexdigest())
        self.assertEqual([r.ordinal for r in parsed.source_rows],[1,2,3])
        self.assertEqual([r.amount for r in parsed.source_rows],[-2000,-2000,5000])
        self.assertEqual(parsed.source_rows[2].bank_reference,'bank-123')
        self.assertEqual(parsed.source_rows[2].booking_status,'booked')

    def test_repeated_bank_reference_inside_file_requires_explicit_choice(self):
        self.preview(rows=[(-2000,'Shop','groceries','same-bank-ref'),(-2000,'Shop','groceries','same-bank-ref')])
        data=self.create()
        self.assertEqual(data['unresolved'],1)
        self.assertEqual(self.apply(data).status_code,422)
        first,second=data['review']['rows']
        resolved=self.call(f"/v2/reviews/{data['review']['id']}/rows/{second['source_id']}/resolve",
            {'revision':data['revision'],'review_version':0,'decision':'link','linked_id':first['source_id']},key='within-file-resolve')
        self.assertEqual(resolved.status_code,200,resolved.text)
        self.assertEqual(self.apply(resolved.json(),'within-file-apply').status_code,200)
        state=self.store.read('A')
        self.assertEqual(len(state.transactions),1)
        self.assertEqual(len(state.reconciliation.ledger[0].source_ids),2)
        self.assertEqual(len(state.reconciliation.reviews[0].rows),2)

    def test_method_change_does_not_reuse_old_parsed_ordinal_identity(self):
        self.preview();first=self.create();self.apply(first)
        parsed=self.preview('new-method',checksum='a'*64)
        # A changed parser may discover new rows; source ordinal is version-scoped.
        parsed.source_method_version='parsed-source-v2'
        with self.store.engine.begin() as conn:
            from vela.store import previews
            conn.execute(previews.update().where(previews.c.owner=='A',previews.c.id=='new-method').values(payload=parsed.model_dump_json()))
        second=self.create('new-method',key='new-method-review')
        self.assertNotEqual(first['review']['rows'][1]['source_id'],second['review']['rows'][1]['source_id'])
        self.assertEqual(second['review']['rows'][1]['decision'],'unresolved')

    def test_actual_factory_legacy_apply_cannot_bypass_new_review(self):
        from vela.main import create_app
        folder=Path(self.temp.name)/'factory'
        app=create_app(f'sqlite:///{Path(self.temp.name)/"factory-reconciliation.db"}',
                       'synthetic-reconciliation-factory-token',local_dir=folder,today=lambda:self.day)
        try:
            original_store=self.store
            self.store=app.state.store
            self.store.mutate('local-demo','seed-local',0,{'kind':'seed'},lambda s:s.personal.accounts.append(
                Account(id='eur',name='Synthetic',currency='EUR',balance=100000,confirmed_on=self.day)),lambda s:{})
            self.preview(who='local-demo')
            auth={'Authorization':'Bearer synthetic-reconciliation-factory-token','Idempotency-Key':'factory-review-create'}
            with TestClient(app) as client:
                response=client.post('/v2/imports/preview-1/review',headers=auth,json={'revision':1,'account_id':'eur'})
                self.assertEqual(response.status_code,200,response.text)
                for prefix in ('v1','v2'):
                    response=client.post(f'/{prefix}/imports/preview-1/apply',headers={**auth,'Idempotency-Key':prefix+'-blocked-apply'},json={'revision':2})
                    self.assertEqual(response.status_code,409,response.text)
                self.assertEqual(app.state.store.read('local-demo').personal.accounts[0].balance,100000)
                self.assertEqual(app.state.store.read('local-demo').transactions,[])
        finally:
            self.store=original_store
            app.state.store.engine.dispose()

    def test_legacy_apply_other_preview_and_cached_receipt_cannot_write_second_ledger(self):
        from vela.main import create_app
        for prefix in ('v1','v2'):
            with self.subTest(prefix=prefix):
                folder=Path(self.temp.name)/('legacy-guard-'+prefix)
                app=create_app(f'sqlite:///{folder.with_suffix(".db")}',
                    'synthetic-reconciliation-factory-token',local_dir=folder,today=lambda:self.day)
                original_store=self.store
                self.store=app.state.store
                try:
                    def seed(state):
                        state.snapshot=fixture(self.day)
                        state.personal.accounts=[Account(id='eur',name='Synthetic',currency='EUR',balance=100000,confirmed_on=self.day)]
                    self.store.mutate('local-demo','seed-local',0,{'kind':'seed'},seed,lambda state:{})
                    for preview_id in ('old-source','review-source','new-source'):
                        self.preview(preview_id,who='local-demo')
                    auth={'Authorization':'Bearer synthetic-reconciliation-factory-token'}
                    cached_key=prefix+'-old-import-key'
                    with TestClient(app) as client:
                        first=client.post(f'/{prefix}/imports/old-source/apply',headers={**auth,'Idempotency-Key':cached_key},json={'revision':1})
                        self.assertEqual(first.status_code,200,first.text)
                        created=client.post('/v2/imports/review-source/review',headers={**auth,'Idempotency-Key':'new-canonical-review'},json={'revision':2,'account_id':'eur'})
                        self.assertEqual(created.status_code,200,created.text)
                        before=self.store.read('local-demo').model_dump_json()
                        for source,key,revision in (('old-source',cached_key,1),('new-source','new-unmanaged-import',3)):
                            blocked=client.post(f'/{prefix}/imports/{source}/apply',headers={**auth,'Idempotency-Key':key},json={'revision':revision})
                            self.assertEqual(blocked.status_code,409,blocked.text)
                            self.assertEqual(self.store.read('local-demo').model_dump_json(),before)
                finally:
                    self.store=original_store
                    app.state.store.engine.dispose()

    def test_legacy_cached_apply_guard_observes_other_store_transition_inside_transaction(self):
        from vela.main import create_app
        for prefix in ('v1','v2'):
            with self.subTest(prefix=prefix):
                folder=Path(self.temp.name)/('legacy-race-'+prefix)
                url=f'sqlite:///{folder.with_suffix(".db")}'
                app=create_app(url,'synthetic-reconciliation-factory-token',local_dir=folder,today=lambda:self.day)
                second=Store(url)
                original_store=self.store
                self.store=app.state.store
                try:
                    self.store.mutate('local-demo','seed-local',0,{'kind':'seed'},lambda state:setattr(state,'snapshot',fixture(self.day)),lambda state:{})
                    self.preview('old-source',who='local-demo')
                    auth={'Authorization':'Bearer synthetic-reconciliation-factory-token','Idempotency-Key':'legacy-race-cached-key'}
                    with TestClient(app) as client:
                        first=client.post(f'/{prefix}/imports/old-source/apply',headers=auth,json={'revision':1})
                        self.assertEqual(first.status_code,200,first.text)
                        original_mutate=self.store.mutate
                        expected=[]
                        def transition_then_mutate(*args,**kwargs):
                            def transition(state):
                                state.reconciliation=ReconciliationState(reviews=[ImportReview(id='new-review',preview_id='another-source',checksum='a'*64,account_id='eur',currency='EUR')])
                            second.mutate('local-demo','separate-store-review',2,{'kind':'synthetic-review-transition'},transition,lambda state:{})
                            expected.append(second.read('local-demo').model_dump_json())
                            return original_mutate(*args,**kwargs)
                        with patch.object(self.store,'mutate',side_effect=transition_then_mutate):
                            blocked=client.post(f'/{prefix}/imports/old-source/apply',headers=auth,json={'revision':1})
                        self.assertEqual(blocked.status_code,409,blocked.text)
                        self.assertEqual(self.store.read('local-demo').model_dump_json(),expected[0])
                finally:
                    self.store=original_store
                    second.engine.dispose()
                    app.state.store.engine.dispose()

    def test_correction_does_not_silently_resolve_repeated_bank_reference(self):
        self.preview(rows=[(-2000,'Shop','groceries','same-ref'),(-2000,'Shop','groceries','same-ref')])
        data=self.create()
        row=data['review']['rows'][1]
        corrected=self.call(f"/v2/reviews/{data['review']['id']}/rows/{row['source_id']}",
            {'revision':data['revision'],'review_version':0,'category':'shopping','reason':'Correct category'},
            method='PUT',key='correct-duplicate-category')
        self.assertEqual(corrected.status_code,200,corrected.text)
        data=corrected.json()
        self.assertEqual(data['unresolved'],1)
        self.assertEqual(data['review']['rows'][1]['decision'],'unresolved')
        self.assertEqual(data['review']['rows'][1]['effective']['category_method'],'manual_correction')
        self.assertEqual(data['review']['rows'][1]['original']['category_method'],'legacy_unspecified')
        self.assertEqual(self.apply(data,'still-needs-duplicate-choice').status_code,422)
        self.assertEqual(self.store.read('A').transactions,[])
