import React, { useState } from 'react';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Copy, Loading, Notice, Row, Screen } from '../components/ui';
import { ObservationsView } from '../lib/generated';
import { money, request, Transaction } from '../lib/api';

export default function ObservationsScreen() {
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState('');
  const [history, setHistory] = useState(false);
  const [offset, setOffset] = useState(0);
  const data = useQuery({queryKey: ['observations'], queryFn: () => request<ObservationsView>('/v2/observations')});
  const evidence = useQuery({queryKey: ['observation-evidence', data.data?.revision], queryFn: () => request<{transactions: Transaction[]}>('/v1/transactions?limit=3000'), enabled: Boolean(selected)});
  const observation = data.data?.observations.find(o => o.id === selected);
  const transactions = useQuery({queryKey: ['analytical-history', data.data?.revision, offset], queryFn: () => request<{transactions: Transaction[]; total: number}>(`/v1/transactions?limit=50&offset=${offset}`), enabled: history});
  return <Screen title="Statement patterns" eyebrow="Recorded evidence · EUR">
    <Button label="Your saved accounts" secondary onPress={() => router.push('/personal')} />
    <Button label="Upload statement" onPress={() => router.push('/import')} />
    <Button label={history ? 'Return to patterns' : 'View all imported transactions'} secondary onPress={() => {setHistory(!history); setSelected('');}} />
    {data.isPending ? <Loading /> : data.error ? <><Notice>{data.error.message}</Notice><Button label="Try again" onPress={() => {void data.refetch();}} /></> : data.data && <>
      <Copy muted>{data.data.transaction_count} recorded transactions · {data.data.period_start ?? 'No period'} → {data.data.period_end ?? 'No period'} · data version {data.data.revision}</Copy>
      <Notice>Suggestions only. Coverage may be partial. Nothing here changes money or creates a bill; a recurring payment does not mean a service is unnecessary.</Notice>
      {data.data.observations.length === 0 && <Copy>No repeated pattern supported by the recorded rows yet. You can add another statement.</Copy>}
      {history ? <Card>
        <Copy variant="title">Imported transactions</Copy>
        {transactions.isPending ? <Loading /> : transactions.error ? <><Notice>{transactions.error.message}</Notice><Button label="Retry transactions" onPress={() => {void transactions.refetch();}} /></> : (transactions.data?.transactions ?? []).map(t => <Row key={t.id} label={`${t.date} · ${t.description} (${t.category})`} value={money(t.amount)} />)}
        <Copy muted>Page {Math.floor(offset / 50) + 1} of {Math.max(1, Math.ceil((transactions.data?.total ?? data.data.transaction_count) / 50))}</Copy>
        <Button label="Previous transactions" secondary disabled={offset === 0 || transactions.isFetching} onPress={() => setOffset(Math.max(0, offset - 50))} />
        <Button label="Next transactions" secondary disabled={offset + 50 >= (transactions.data?.total ?? data.data.transaction_count) || transactions.isFetching} onPress={() => setOffset(offset + 50)} />
      </Card> : observation ? <Card>
        <Copy variant="title">{observation.label}</Copy><Copy>{observation.note}</Copy>
        <Copy muted>{observation.method_version} · {observation.evidence_ids.length} source entries</Copy>
        {evidence.isPending ? <Loading /> : evidence.error ? <><Notice>{evidence.error.message}</Notice><Button label="Retry supporting transactions" onPress={() => {void evidence.refetch();}} /></> : (evidence.data?.transactions ?? []).filter(t => observation.evidence_ids.includes(t.id)).map(t => <Row key={t.id} label={`${t.date} · ${t.description}`} value={money(t.amount)} />)}
        <Button label="Back to patterns" secondary onPress={() => setSelected('')} />
      </Card> : <>
        {data.data.observations.slice(page * 10, page * 10 + 10).map(o => <Card key={o.id}>
          <Copy variant="title">{o.label}</Copy><Copy muted>{o.kind.replaceAll('_', ' ')} · Suggested</Copy>
          <Copy>{o.note}</Copy>
          {o.amounts.slice(0, 6).map((amount, i) => <Row key={`${o.id}-${i}`} label={o.periods[i] ?? 'Recorded entry'} value={money(amount)} />)}
          {o.difference != null && <Row label="Latest recorded amount change" value={money(o.difference)} />}
          <Button label={`Show supporting transactions for ${o.label}`} secondary onPress={() => setSelected(o.id)} />
        </Card>)}
        <Copy muted>Page {page + 1} of {Math.max(1, Math.ceil(data.data.observations.length / 10))}</Copy>
        <Button label="Previous patterns" secondary disabled={page === 0} onPress={() => setPage(page - 1)} />
        <Button label="Next patterns" secondary disabled={(page + 1) * 10 >= data.data.observations.length} onPress={() => setPage(page + 1)} />
      </>}
    </>}
  </Screen>;
}
