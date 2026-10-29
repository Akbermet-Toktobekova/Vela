import React, { useEffect, useRef, useState } from 'react';
import { router } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { SharedNavigation } from '../components/SharedNavigation';
import { Button, Card, Chip, Copy, Field, Loading, Notice, Row, Screen } from '../components/ui';
import { PersonalView, PlanningView, PreviewStepView } from '../lib/generated';
import { cents, localDate, money, request } from '../lib/api';

const identity = () => `shared-${Date.now()}-${Math.random().toString(36).slice(2)}`;
function days(value: string) {
  if (!/^\d{1,2}$/.test(value) || Number(value) > 93) throw new Error('Enter a whole number of days from0 to93.');
  return Number(value);
}

export default function SharedPlanScreen() {
  const cache = useQueryClient();
  const query = useQuery({queryKey: ['shared-plan'], queryFn: () => request<PlanningView>('/v2/planning')});
  const accounts = useQuery({queryKey: ['personal'], queryFn: () => request<PersonalView>('/v2/personal')});
  const [editing, setEditing] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [accountId, setAccountId] = useState('');
  const [buffer, setBuffer] = useState('');
  const [length, setLength] = useState('30');
  const [goalName, setGoalName] = useState('');
  const [target, setTarget] = useState('');
  const [billsConfirmed, setBillsConfirmed] = useState(false);
  const [debtsConfirmed, setDebtsConfirmed] = useState(false);
  const [legacyConfirmed, setLegacyConfirmed] = useState(false);
  const [amount, setAmount] = useState('');
  const [addBill, setAddBill] = useState(false);
  const [billName, setBillName] = useState('');
  const [billAmount, setBillAmount] = useState('');
  const [billDays, setBillDays] = useState('7');
  const [payId, setPayId] = useState('');
  const [payEffect, setPayEffect] = useState('');
  const [complete, setComplete] = useState(false);
  const [error, setError] = useState('');
  const retry = useRef<{signature: string; key: string} | null>(null);
  const billId = useRef(identity());
  const stepId = useRef(identity());
  const preview = useMutation({mutationFn: (text: string) => request<PreviewStepView>('/v2/planning/preview', 'POST', {amount: cents(text)})});
  const mutation = useMutation({
    mutationFn: ({path, method = 'POST', fields = {}}: {path: string; method?: string; fields?: Record<string, unknown>}) => {
      if (!query.data) throw new Error('Load your current plan first.');
      const body = {revision: query.data.revision, ...fields};
      const signature = JSON.stringify({path, method, body});
      if (retry.current?.signature !== signature) retry.current = {signature, key: identity()};
      return request<PlanningView>(path, method, body, retry.current.key);
    },
    onSuccess: data => {
      cache.setQueryData(['shared-plan'], data); void cache.invalidateQueries();
      retry.current = null; setEditing(false); setError(''); setComplete(false); setPayId(''); setPayEffect('');
      setAddBill(false); setBillName(''); setBillAmount(''); billId.current = identity(); stepId.current = identity();
      preview.reset();
    },
  });
  useEffect(() => {
    if (query.data && !initialized) {
      const p = query.data.planning;
      setAccountId(p.account_id ?? ''); setBuffer(p.protected == null ? '' : String(p.protected / 100));
      if (p.horizon) setLength(String(Math.max(0, Math.round((Date.parse(`${p.horizon}T00:00:00Z`) - Date.parse(`${localDate()}T00:00:00Z`)) / 86400000))));
      setGoalName(p.goal?.name ?? ''); setTarget(p.goal ? String(p.goal.target / 100) : '');
      setBillsConfirmed(p.bills_confirmed ?? false); setDebtsConfirmed(p.debts_confirmed ?? false); setInitialized(true);
    }
  }, [query.data, initialized]);
  const busy = mutation.isPending;
  const change = (setter: (s: string) => void) => (value: string) => {if (!busy) {setter(value); setError(''); mutation.reset();}};
  const submit = (action: () => void) => {if (!busy) {try {setError(''); action();} catch (e) {setError(e instanceof Error ? e.message : 'Check your entry.');}}};
  if (query.isPending || accounts.isPending) return <Loading />;
  if (!query.data || !accounts.data) return <Screen title="My Plan"><Notice>{query.error?.message ?? accounts.error?.message ?? 'Your plan could not be loaded.'}</Notice><Button label="Try again" onPress={() => {void query.refetch(); void accounts.refetch();}} /></Screen>;
  const data = query.data, p = data.planning;
  const step = p.steps?.find(s => s.status === 'planned');
  const eligiblePreview = preview.isSuccess && preview.variables === amount && preview.data.eligible && preview.data.revision === data.revision;
  return <Screen title="My Plan" eyebrow="Your saved EUR account">
    <SharedNavigation current="plan" />
    <Copy muted>This local plan uses one chosen EUR account. HUF balances stay separate; no exchange rate or bank transfer is assumed.</Copy>
    {Boolean(error || mutation.error || preview.error) && <Notice>{error || mutation.error?.message || preview.error?.message}</Notice>}
    {mutation.isError && <Button label="Refresh plan after a conflict" secondary onPress={() => {void query.refetch(); void accounts.refetch(); mutation.reset();}} />}
    {!p.active || editing ? <Card>
      <Copy variant="title">{p.active ? 'Review planning inputs' : 'Choose your planning account'}</Copy>
      {p.active ? <Copy>{data.account?.name} · EUR · balance managed on Today</Copy> : <>
        {(accounts.data.data.accounts ?? []).filter(a => a.currency === 'EUR').map(a => <Chip key={a.id} label={`${a.name} · ${a.balance == null ? 'Not provided' : money(a.balance)} · ${a.confirmed_on ?? 'not confirmed'}`} active={a.id === accountId} onPress={() => {if (!busy) setAccountId(a.id);}} />)}
        <Button label="Manage accounts" secondary disabled={busy} onPress={() => router.push('/personal')} />
      </>}
      {data.legacy && !p.active ? <>
        <Notice>Your previous plan remains unchanged until you review and adopt it. The chosen account must have the same freshly confirmed balance.</Notice>
        <Row label="Legacy cash" value={money(data.legacy.cash)} /><Row label="Legacy goal allocation" value={money(data.legacy.saved)} />
        <Copy>{data.legacy.goal_name} · target {money(data.legacy.goal_target)} · {data.legacy.bill_count} bills · {data.legacy.planned_count} active steps</Copy>
        <Button label="Review legacy workspace" secondary disabled={busy} onPress={() => router.push('/')} />
        <Chip label="I reviewed the legacy goal, allocations and bills" active={legacyConfirmed} onPress={() => {if (!busy) setLegacyConfirmed(!legacyConfirmed);}} />
        <Button label="Adopt reviewed legacy plan" loading={busy} disabled={!accountId || !legacyConfirmed} onPress={() => mutation.mutate({path: '/v2/planning/adopt-legacy', fields: {account_id: accountId, confirm_finances: legacyConfirmed}})} />
      </> : <>
        <Field label="Plan length in days (0–93)" numeric value={length} onChangeText={change(setLength)} helper={`Plan through ${/^\d{1,2}$/.test(length) ? localDate(Number(length)) : 'choose days'}`} />
        <Field label="Protected money (EUR)" numeric value={buffer} onChangeText={change(setBuffer)} helper="Leave empty if unknown. Zero means you explicitly chose no protected amount." />
        <Field label="Goal name (optional)" value={goalName} onChangeText={change(setGoalName)} />
        <Field label="Goal target (EUR, optional)" numeric value={target} onChangeText={change(setTarget)} helper="No goal is created unless you enter both name and target. Existing allocations are preserved." />
        <Chip label={billsConfirmed ? 'All necessary bills included' : 'Bills still need checking'} active={billsConfirmed} onPress={() => {if (!busy) setBillsConfirmed(!billsConfirmed);}} />
        <Chip label={debtsConfirmed ? 'Required debt payments checked' : 'Debt payments still need checking'} active={debtsConfirmed} onPress={() => {if (!busy) setDebtsConfirmed(!debtsConfirmed);}} />
        <Button label="Save account plan" loading={busy} onPress={() => submit(() => {
          if (!accountId) throw new Error('Choose an EUR account.');
          if (Boolean(goalName.trim()) !== Boolean(target.trim())) throw new Error('Enter both goal name and target, or leave both empty.');
          mutation.mutate({path: '/v2/planning', method: 'PUT', fields: {account_id: accountId, horizon: localDate(days(length)), protected: buffer.trim() ? cents(buffer) : null, bills_confirmed: billsConfirmed, debts_confirmed: debtsConfirmed, goal: goalName.trim() ? {name: goalName.trim(), target: cents(target)} : null}});
        })} />
      </>}
      {p.active && <Button label="Back without saving" secondary disabled={busy} onPress={() => {setEditing(false); setInitialized(false);}} />}
    </Card> : <>
      <Card>
        <Copy variant="title">{data.account?.name}</Copy><Row label={`Balance · ${data.account?.confirmed_on ?? 'not confirmed'}`} value={data.cash == null ? 'Not provided' : money(data.cash)} />
        <Row label="Earmarked for goal" value={money(data.goal_saved)} /><Row label="Protected" value={p.protected == null ? 'Not confirmed' : money(p.protected)} />
        <Row label="Recorded unpaid bills" value={money(data.known_bills)} /><Row label="Reserved by accepted step" value={money(data.reserved)} />
        <Row label="Available through plan date" value={data.available == null ? 'Needs confirmation' : money(data.available)} bold />
        <Notice>{data.message}</Notice>
        <Button label="Review planning inputs" secondary disabled={busy} onPress={() => {setInitialized(false); setEditing(true);}} />
        <Button label="Update account balance or income" secondary onPress={() => router.push('/personal')} />
      </Card>
      {p.goal && <Card><Copy variant="title">{p.goal.name}</Copy><Row label="Earmarked / target" value={`${money(data.goal_saved)} / ${money(p.goal.target)}`} /><Copy muted>Allocating money here does not transfer it. A lower real balance may require reviewing this allocation.</Copy></Card>}
      {step ? <Card>
        <Copy variant="title">Accepted step · {money(step.amount)}</Copy>
        {complete ? <><Notice>Confirm only after you have earmarked this amount yourself. This records an allocation; Vela does not move money.</Notice><Button label="Confirm earmarked" loading={busy} disabled={!data.can_complete} onPress={() => mutation.mutate({path: `/v2/planning/steps/${step.id}/complete`})} /><Button label="Back" secondary disabled={busy} onPress={() => setComplete(false)} /></> : <Button label="Mark earmarked" disabled={!data.can_complete || busy} onPress={() => setComplete(true)} />}
        {!data.can_complete && <Notice>Update or review the plan before completing this step. You can still cancel its reservation.</Notice>}
        <Button label="Cancel accepted step" secondary loading={busy} onPress={() => mutation.mutate({path: `/v2/planning/steps/${step.id}/cancel`})} />
      </Card> : p.goal && <Card>
        <Copy variant="title">Preview a saving step</Copy>
        {data.recommendation_amount != null && data.recommendation_amount > 0 && <Button label={`Use provisional suggestion ${money(data.recommendation_amount)}`} secondary onPress={() => {if (!busy) {setAmount(String(data.recommendation_amount! / 100)); preview.reset();}}} />}
        <Field label="Step amount (EUR)" numeric value={amount} onChangeText={v => {if (!busy) {setAmount(v); preview.reset(); setError('');}}} />
        <Button label="Check step amount" loading={preview.isPending} disabled={busy} onPress={() => preview.mutate(amount)} />
        {preview.data && preview.variables === amount && <><Notice>{preview.data.message}</Notice><Row label="Free after this step" value={preview.data.remaining == null ? 'Unknown' : money(preview.data.remaining)} /></>}
        {preview.isSuccess && preview.data.revision !== data.revision && <Notice>Your information changed. Check the amount again.</Notice>}
        <Button label="Accept saving step" loading={busy} disabled={!eligiblePreview} onPress={() => {if (eligiblePreview) mutation.mutate({path: '/v2/planning/steps', fields: {id: stepId.current, amount: cents(amount)}});}} />
        <Button label="Skip for now" secondary disabled={busy} onPress={() => mutation.mutate({path: '/v2/planning/defer'})} />
      </Card>}
      <Card>
        <Copy variant="title">Confirmed bills</Copy>
        {(p.bills ?? []).filter(b => b.status === 'unpaid').map(b => <Card key={b.id}>
          <Row label={`${b.label} · ${b.due}`} value={money(b.amount)} />
          {payId === b.id ? <>
            <Copy>Is this payment already reflected in the current account balance?</Copy>
            <Chip label="No — subtract this payment" active={payEffect === 'subtract'} onPress={() => {if (!busy) setPayEffect('subtract');}} />
            <Chip label="Yes — record payment only" active={payEffect === 'already_in_balance'} onPress={() => {if (!busy) setPayEffect('already_in_balance');}} />
            <Button label="Confirm bill paid" loading={busy} disabled={!payEffect} onPress={() => mutation.mutate({path: `/v2/planning/bills/${b.id}/pay`, fields: {effect: payEffect}})} />
            <Button label="Keep bill unpaid" secondary disabled={busy} onPress={() => {setPayId(''); setPayEffect('');}} />
          </> : <Button label={`Record ${b.label} as paid`} secondary disabled={busy} onPress={() => {setPayId(b.id); setPayEffect('');}} />}
          <Button label={`Cancel bill ${b.label}`} secondary disabled={busy} onPress={() => mutation.mutate({path: `/v2/planning/bills/${b.id}/cancel`})} />
        </Card>)}
        <Button label={addBill ? 'Close bill draft' : 'Add confirmed bill'} secondary disabled={busy} onPress={() => {setAddBill(!addBill); billId.current = identity(); setError('');}} />
        {addBill && <>
          <Field label="Bill name" value={billName} onChangeText={change(setBillName)} /><Field label="Bill amount (EUR)" numeric value={billAmount} onChangeText={change(setBillAmount)} />
          <Field label="Bill due in days (0 today)" numeric value={billDays} onChangeText={change(setBillDays)} />
          <Button label="Save confirmed bill" loading={busy} onPress={() => submit(() => {
            if (!billName.trim()) throw new Error('Enter a bill name.');
            mutation.mutate({path: '/v2/planning/bills', fields: {id: billId.current, label: billName.trim(), amount: cents(billAmount), currency: 'EUR', due: localDate(days(billDays))}});
          })} />
        </>}
      </Card>
      <Button label="Manage recorded EUR debts" secondary onPress={() => router.push('/debts')} />
      <Button label="Learn about money" secondary onPress={() => router.push('/learn')} />
      <Card><Copy variant="title">Step history</Copy>{(p.steps ?? []).filter(s => s.status !== 'planned').map(s => <Row key={s.id} label={`${s.status} · ${s.completed_on ?? s.created_on}`} value={money(s.amount)} />)}</Card>
    </>}
  </Screen>;
}
