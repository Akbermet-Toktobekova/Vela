import React, { useRef, useState } from 'react';
import { router } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Chip, Copy, Field, Loading, Notice, Row, Screen } from '../components/ui';
import { localDate, cents, request } from '../lib/api';
import { PersonalView } from '../lib/generated';
import { useConnection } from '../lib/state';

type Page = 'today' | 'profile' | 'account' | 'balance' | 'income';
const focusChoices = [{id: 'spending', label: 'Understand my spending'}, {id: 'reserve', label: 'Build a cushion'}, {id: 'debt', label: 'Manage debt'}, {id: 'goal', label: 'Save for something'}, {id: 'unsure', label: 'Not sure yet'}];
export default function PersonalScreen() {
  const {connected, ready} = useConnection();
  const cache = useQueryClient();
  const [page, setPage] = useState<Page>('today');
  const [focus, setFocus] = useState('unsure');
  const [incomeType, setIncomeType] = useState('unknown');
  const [name, setName] = useState('Main account');
  const [currency, setCurrency] = useState('EUR');
  const [input, setInput] = useState('');
  const [replacement, setReplacement] = useState('');
  const [selected, setSelected] = useState('');
  const [effect, setEffect] = useState('');
  const [error, setError] = useState('');
  const retry = useRef<{signature: string; key: string} | null>(null);
  const query = useQuery({queryKey: ['personal'], queryFn: () => request<PersonalView>('/v2/personal'), enabled: connected});
  const mutation = useMutation({
    mutationFn: ({path, method, body}: {path: string; method: string; body: unknown}) => {
      const signature = JSON.stringify({path, method, body});
      if (retry.current?.signature !== signature) retry.current = {signature, key: `personal-${Date.now()}-${Math.random().toString(36).slice(2)}`};
      return request<PersonalView>(path, method, body, retry.current.key);
    },
    onSuccess: data => {retry.current = null; cache.setQueryData(['personal'], data); void cache.invalidateQueries({queryKey: ['personal']}); void cache.invalidateQueries({queryKey: ['state']}); setPage('today'); setInput(''); setError('');},
  });
  if (!ready || query.isPending && connected) return <Loading />;
  if (!connected) return <Screen title="Your Vela"><Notice>Connect to your local server to save your information.</Notice><Button label="Connect" onPress={() => router.push('/connect')} /></Screen>;
  if (!query.data) return <Screen title="Your Vela"><Notice>{query.error?.message ?? 'Your information could not be loaded.'}</Notice><Button label="Try again" onPress={() => {void query.refetch();}} /></Screen>;
  const state = query.data;
  const accounts = state.data.accounts ?? [];
  const account = accounts.find(a => a.id === selected);
  const busy = mutation.isPending;
  const open = (next: Page, id = '') => {setPage(next); setSelected(id); setInput(''); setEffect(''); setReplacement(''); setError(''); mutation.reset();};
  const save = () => {
    if (busy) return;
    try {
      const base = {revision: state.revision};
      if (page === 'profile') mutation.mutate({path: '/v2/profile', method: 'PUT', body: {...base, focus, income_type: incomeType}});
      else if (page === 'account') {
        if (!name.trim()) throw new Error('Enter an account name.');
        mutation.mutate({path: '/v2/accounts', method: 'POST', body: {...base, name: name.trim(), currency, balance: input.trim() ? cents(input) : null, confirmed_on: localDate()}});
      } else if (page === 'balance') {
        if (!account) throw new Error('Choose an account.');
        mutation.mutate({path: `/v2/accounts/${account.id}/balance`, method: 'PUT', body: {...base, balance: cents(input), confirmed_on: localDate()}});
      } else if (page === 'income') {
        if (!account || !effect) throw new Error('Choose an account and how this income affects your balance.');
        const value = cents(input);
        if (value <= 0) throw new Error('Enter an income above zero.');
        mutation.mutate({path: '/v2/income', method: 'POST', body: {...base, account_id: account.id, amount: value, received_on: localDate(), effect, current_balance: effect === 'replace' ? cents(replacement) : null}});
      }
    } catch (e) {setError(e instanceof Error ? e.message : 'Check your entry.');}
  };
  return <Screen title={page === 'today' ? 'Your Today' : page === 'profile' ? 'What matters to you' : page === 'account' ? 'Add an account' : page === 'balance' ? 'Update balance' : 'Add income'} eyebrow="Vela · saved locally">
    <Copy muted>Saved on your connected local server. Cloud sign-in and recommendations are not connected yet.</Copy>
    {page !== 'today' && <Button label="Back to Today" secondary disabled={busy} onPress={() => open('today')} />}
    {page === 'today' ? <>
      {!state.data.onboarded && <Card soft><Copy variant="title">Start with what matters</Copy><Copy>Tell us what you want help with. A statement is optional.</Copy><Button label="Set up my profile" onPress={() => open('profile')} /></Card>}
      {accounts.length === 0 ? <Card><Copy variant="title">Your money starts here</Copy><Copy muted>Add a known balance or leave it unknown. No example amounts are added.</Copy></Card> : accounts.map(a => <Card key={a.id}>
        <Copy variant="title">{a.name}</Copy><Copy variant="money">{a.balance === null || a.balance === undefined ? 'Not provided' : new Intl.NumberFormat('en-IE', {style: 'currency', currency: a.currency}).format(a.balance / 100)}</Copy>
        <Copy muted>{a.confirmed_on ? `Confirmed ${a.confirmed_on}` : 'Balance not confirmed'}</Copy>
        <Button label={`Add income to ${a.name}`} onPress={() => open('income', a.id)} /><Button label={`Update ${a.name} balance`} secondary onPress={() => open('balance', a.id)} />
      </Card>)}
      <Button label="Add account" onPress={() => open('account')} />
      <Button label="Edit profile" secondary onPress={() => {setFocus(state.data.focus ?? 'unsure'); setIncomeType(state.data.income_type ?? 'unknown'); open('profile');}} />
      <Button label="Refresh saved data" secondary onPress={() => {void query.refetch();}} />
      <Row label="Income records" value={String(state.data.incomes?.length ?? 0)} />
      <Notice>Balances stay separate by currency. Missing exchange rates are not treated as zero. Planning will be connected after obligations and goals.</Notice>
    </> : <Card>
      {page === 'profile' ? <>
        <Copy variant="title">What would you like help with?</Copy>{focusChoices.map(c => <Chip key={c.id} label={c.label} active={focus === c.id} onPress={() => {if (!busy) setFocus(c.id);}} />)}
        <Copy variant="title">How does your income arrive?</Copy>{['regular', 'irregular', 'mixed', 'unknown'].map(c => <Chip key={c} label={c === 'unknown' ? 'Not sure yet' : c} active={incomeType === c} onPress={() => {if (!busy) setIncomeType(c);}} />)}
      </> : <>
        {page === 'account' && <><Field label="Account name" value={name} onChangeText={v => {if (!busy) setName(v);}} />{['EUR', 'HUF'].map(c => <Chip key={c} label={c} active={currency === c} onPress={() => {if (!busy) setCurrency(c);}} />)}</>}
        {account && <Copy>{account.name} · {account.currency} · current balance: {account.balance === null || account.balance === undefined ? 'unknown' : new Intl.NumberFormat('en-IE', {style: 'currency', currency: account.currency}).format(account.balance / 100)}</Copy>}
        <Field label={`${page === 'income' ? 'Income received' : 'Current balance'} (${account?.currency ?? currency})`} numeric value={input} onChangeText={v => {if (!busy) {setInput(v); setError('');}}} helper={page === 'account' ? 'Leave empty if unknown.' : 'Enter the amount in currency units, not cents.'} />
        {page === 'income' && <><Copy>Is this income already in your balance?</Copy>{[{id: 'add', label: 'No — add it'}, {id: 'included', label: 'Yes — record only'}, {id: 'replace', label: 'Not sure — enter current balance'}].map(c => <Chip key={c.id} label={c.label} active={effect === c.id} onPress={() => {if (!busy) setEffect(c.id);}} />)}{effect === 'replace' && <Field label="Current account balance" numeric value={replacement} onChangeText={v => {if (!busy) setReplacement(v);}} />}</>}
        {page === 'balance' && <Copy muted>Replaces the known balance. The difference is not recorded as income or spending.</Copy>}
      </>}
      {Boolean(error || mutation.error) && <Notice>{error || mutation.error?.message}</Notice>}
      <Button label="Save" loading={busy} onPress={save} />
      {mutation.isError && <Button label="Refresh after a conflict" secondary onPress={() => {void query.refetch(); mutation.reset();}} />}
    </Card>}
  </Screen>;
}
