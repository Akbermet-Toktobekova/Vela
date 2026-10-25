import React, { useState } from 'react';
import { View } from 'react-native';
import { router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { Button, Card, Chip, Copy, Field, Notice, Row, Screen } from '../components/ui';
import { StateGate } from '../components/StateGate';
import { cents, FinancialState, money, Preview, request } from '../lib/api';
import { useCommand } from '../lib/state';
import { space } from '../theme';

function AdjustContent({state}: {state: FinancialState}) {
  const s = state.snapshot!;
  const maxAllowed = Math.max(0, Math.min(state.available, s.goal_target - s.saved));
  const defaultCents = state.recommendation.amount > 0 ? state.recommendation.amount : Math.min(2000, maxAllowed);
  const [amount, setAmount] = useState(String(defaultCents / 100));
  const command = useCommand();
  const preview = useMutation({mutationFn: (value: string) => request<Preview>('/v1/preview', 'POST', {amount: cents(value)})});
  const current = preview.data?.revision === state.revision ? preview.data : undefined;

  const presets = Array.from(new Set([
    Math.min(1000, maxAllowed),
    Math.min(2500, maxAllowed),
    Math.min(5000, maxAllowed),
    Math.floor(maxAllowed / 500) * 500,
    maxAllowed,
  ].filter(v => v >= 500))).slice(0, 4);

  function pickPreset(centsValue: number) {
    const str = String(centsValue / 100);
    setAmount(str);
    preview.mutate(str);
  }

  return <>
    <Card>
      <Copy variant="title">What fits right now</Copy>
      <Row label={`Free until ${s.horizon}`} value={money(state.available)} />
      <Row label="Goal remaining" value={money(Math.max(0, s.goal_target - s.saved))} />
      <Row label="Max step you can plan" value={money(maxAllowed)} bold />
    </Card>

    <Card>
      <Copy variant="title">Choose an amount</Copy>
      {presets.length > 0 && (
        <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
          {presets.map(v => (
            <Chip key={v} label={money(v)} active={amount === String(v / 100)} onPress={() => pickPreset(v)} />
          ))}
        </View>
      )}
      <Field label="Amount in EUR" numeric value={amount} onChangeText={value => {setAmount(value); preview.reset();}} />
      <Button label="Check amount" secondary disabled={preview.isPending} onPress={() => preview.mutate(amount)} />
      {preview.error && <Notice>{preview.error.message}</Notice>}
      {current && <>
        <Row label="Goal after this step" value={money(current.goal_after)} />
        <Row label="Still free" value={money(current.remaining)} />
        <Notice>{current.eligible ? 'This amount fits your current balance and bills.' : 'This amount exceeds what is free or remaining on your goal, or your snapshot needs confirmation first.'}</Notice>
      </>}
      <Button
        label="Add to my plan"
        disabled={command.isPending || (current ? !current.eligible : maxAllowed <= 0)}
        onPress={() => {
          try {
            const value = current ? current.amount : cents(amount);
            command.mutate({path: '/v1/actions', body: {revision: state.revision, amount: value}}, {onSuccess: () => router.replace('/plan')});
          } catch {
            preview.mutate(amount);
          }
        }}
      />
      {command.error && <Notice>{command.error.message}</Notice>}
    </Card>
  </>;
}

export default function AdjustScreen() {
  return <Screen title="Choose amount" eyebrow="Vela"><StateGate>{state => <AdjustContent state={state} />}</StateGate></Screen>;
}
