import React, { useState } from 'react';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery } from '@tanstack/react-query';
import { SharedNavigation } from '../components/SharedNavigation';
import { Button, Card, Copy, Field, Loading, Notice, Row, Screen } from '../components/ui';
import { PlanningView, PreviewStepView } from '../lib/generated';
import { cents, money, request } from '../lib/api';

export default function SharedAssistantScreen() {
  const {revision} = useLocalSearchParams<{revision?: string}>();
  const data = useQuery({queryKey: ['shared-plan'], queryFn: () => request<PlanningView>('/v2/planning')});
  const [amount, setAmount] = useState('');
  const scenario = useMutation({mutationFn: (text: string) => request<PreviewStepView>('/v2/planning/preview', 'POST', {amount: cents(text)})});
  return <Screen title="Assistant" eyebrow="Local explanation · your saved account">
    <SharedNavigation current="assistant" />
    <Copy muted>This explanation reads the same account and plan as Today and My Plan. Model-backed conversation and persistent chat are not connected to this local path yet.</Copy>
    {data.isPending ? <Loading /> : !data.data ? <><Notice>{data.error?.message ?? 'Your plan could not be loaded.'}</Notice><Button label="Try again" onPress={() => {void data.refetch();}} /></> : <>
      {revision != null && String(data.data.revision) !== revision && <Notice>Your information changed since that step. These are the current numbers.</Notice>}
      <Card>
        <Copy variant="title">Why this next step?</Copy><Copy>{data.data.message}</Copy>
        <Copy muted>Data version {data.data.revision} · {data.data.account?.name ?? 'No account selected'} · {data.data.account?.confirmed_on ?? 'Balance not confirmed'}</Copy>
        <Row label="Confirmed account balance" value={data.data.cash == null ? 'Not provided' : money(data.data.cash)} />
        <Row label="Earmarked for goal" value={money(data.data.goal_saved)} /><Row label="Protected" value={data.data.planning.protected == null ? 'Not confirmed' : money(data.data.planning.protected)} />
        <Row label="Recorded unpaid bills" value={money(data.data.known_bills)} /><Row label="Accepted reservation" value={money(data.data.reserved)} />
        <Row label="Available" value={data.data.available == null ? 'Needs confirmation' : money(data.data.available)} />
        <Copy muted>The saving rule is provisional. Statements are historical evidence and do not add cash. No bank transfer is performed.</Copy>
      </Card>
      <Card>
        <Copy variant="title">What if I earmark a different amount?</Copy>
        <Field label="What-if amount (EUR)" numeric value={amount} onChangeText={v => {setAmount(v); scenario.reset();}} />
        <Button label="Preview without changing money" loading={scenario.isPending} onPress={() => scenario.mutate(amount)} />
        {scenario.error && <Notice>{scenario.error.message}</Notice>}
        {scenario.data && <><Notice>{scenario.data.message}</Notice><Row label="Hypothetical free amount" value={scenario.data.remaining == null ? 'Unknown' : money(scenario.data.remaining)} /><Copy muted>No money, plan or goal was changed.</Copy></>}
      </Card>
    </>}
    <Button label="Review my statement patterns" secondary onPress={() => router.push('/observations')} />
    <Button label="Learn about money" secondary onPress={() => router.push('/learn')} />
  </Screen>;
}
