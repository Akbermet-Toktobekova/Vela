import React, { useState } from 'react';
import { View } from 'react-native';
import { router, Href } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Chip, Copy, Field, Notice, Row, Screen } from '../../components/ui';
import { StateGate } from '../../components/StateGate';
import { GoalCard } from '../../components/GoalCard';
import { useCommand } from '../../lib/state';
import { cents, FinancialState, localDate, money, Obligation, request, Transaction } from '../../lib/api';
import { space, usePalette } from '../../theme';

function PlanContent({state}: {state: FinancialState}) {
  const p = usePalette();
  const command = useCommand();
  const [confirm, setConfirm] = useState<string | null>(null);
  const [showAddBill, setShowAddBill] = useState(false);
  const [billLabel, setBillLabel] = useState('');
  const [billAmount, setBillAmount] = useState('');
  const [billDue, setBillDue] = useState(localDate(7));
  const [billKind, setBillKind] = useState<Obligation['kind']>('other');
  const [formError, setFormError] = useState('');
  const [showTxns, setShowTxns] = useState(false);

  const txnsQuery = useQuery({
    queryKey: ['transactions', state.revision],
    queryFn: () => request<{transactions: Transaction[]; total: number}>('/v1/transactions?limit=50'),
    enabled: showTxns && state.summary.transaction_count > 0,
  });

  const s = state.snapshot!;
  const plans = state.actions.filter(a => a.status === 'planned');

  function submitBill() {
    try {
      if (!billLabel.trim()) throw new Error('Enter a bill name.');
      const amount = cents(billAmount);
      if (!amount) throw new Error('Enter an amount above zero.');
      if (!/^\d{4}-\d{2}-\d{2}$/.test(billDue)) throw new Error('Use YYYY-MM-DD for due date.');
      const obligation: Obligation = {id: `bill-${Date.now()}`, label: billLabel.trim(), amount, due: billDue, kind: billKind};
      setFormError('');
      command.mutate({path: '/v1/obligations', body: {revision: state.revision, obligation}}, {
        onSuccess: () => {setBillLabel(''); setBillAmount(''); setShowAddBill(false);},
      });
    } catch (e) {
      setFormError(e instanceof Error ? e.message : 'Check bill fields.');
    }
  }

  return <>
    <GoalCard state={state} />

    {plans.length === 0 ? (
      <Card soft>
        <Copy variant="title">No active step</Copy>
        <Copy muted>Accept a suggestion on Today or choose a custom amount to reserve toward your goal.</Copy>
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}><Button label="Choose amount" small onPress={() => router.push('/adjust')} /></View>
          <View style={{flex: 1}}><Button label="Upload statement" small secondary onPress={() => router.push('/import')} /></View>
        </View>
      </Card>
    ) : plans.map(action => (
      <Card key={action.id} soft>
        <Copy variant="small" muted>Planned · {action.created_on}</Copy>
        <Copy variant="title">Set aside {money(action.amount)}</Copy>
        {!action.can_complete ? (
          <Notice>Your snapshot needs confirmation or free funds dropped below this amount. Check Today first.</Notice>
        ) : confirm === action.id ? <>
          <Notice>Confirm once you have set {money(action.amount)} aside. Vela records the allocation in your goal.</Notice>
          <View style={{flexDirection: 'row', gap: space.sm}}>
            <View style={{flex: 1}}><Button label="Confirm done" small disabled={command.isPending} onPress={() => command.mutate({path: `/v1/actions/${action.id}/complete`, body: {revision: state.revision}}, {onSuccess: () => setConfirm(null)})} /></View>
            <View style={{flex: 1}}><Button label="Back" small secondary onPress={() => setConfirm(null)} /></View>
          </View>
        </> : (
          <View style={{flexDirection: 'row', gap: space.sm}}>
            <View style={{flex: 1}}><Button label="Mark done" small onPress={() => setConfirm(action.id)} /></View>
            <View style={{flex: 1}}><Button label="Cancel step" small secondary disabled={command.isPending} onPress={() => command.mutate({path: `/v1/actions/${action.id}/cancel`, body: {revision: state.revision}})} /></View>
          </View>
        )}
      </Card>
    ))}

    {(command.error || formError) && <Notice>{formError || command.error?.message}</Notice>}

    <Card>
      <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        <Copy variant="title">Unpaid bills ({s.obligations.length})</Copy>
        <Button label={showAddBill ? 'Close' : '+ Add bill'} small secondary onPress={() => setShowAddBill(!showAddBill)} />
      </View>

      {showAddBill && <View style={{gap: space.sm, paddingVertical: space.xs}}>
        <Field label="Bill name" placeholder="e.g. Rent, Electricity, Credit card" value={billLabel} onChangeText={setBillLabel} />
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}><Field label="Amount (EUR)" numeric placeholder="250" value={billAmount} onChangeText={setBillAmount} /></View>
          <View style={{flex: 1}}><Field label={`Due (≤ ${s.horizon})`} value={billDue} onChangeText={setBillDue} /></View>
        </View>
        <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
          {(['rent', 'living', 'debt', 'other'] as const).map(k => (
            <Chip key={k} label={k} active={billKind === k} onPress={() => setBillKind(k)} />
          ))}
        </View>
        <Button label="Save bill" small disabled={command.isPending} onPress={submitBill} />
      </View>}

      {s.obligations.length === 0 && <Copy variant="small" muted>No unpaid bills listed through {s.horizon}.</Copy>}
      {s.obligations.map(o => (
        <View key={o.id} style={{paddingVertical: space.xs, borderBottomWidth: 0.5, borderColor: p.border, gap: 4}}>
          <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
            <Copy>{o.label} · <Copy variant="small" muted>{o.due} ({o.kind})</Copy></Copy>
            <Copy variant="title">{money(o.amount)}</Copy>
          </View>
          <View style={{flexDirection: 'row', gap: space.xs}}>
            <Button label="Mark paid (−cash)" small secondary disabled={command.isPending}
              onPress={() => command.mutate({path: `/v1/obligations/${o.id}/done`, body: {revision: state.revision, paid: true}})} />
            <Button label="Remove" small secondary disabled={command.isPending}
              onPress={() => command.mutate({path: `/v1/obligations/${o.id}/done`, body: {revision: state.revision, paid: false}})} />
          </View>
        </View>
      ))}
    </Card>

    <Card>
      <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        <Copy variant="title">Debts & payoff ({(state.debts ?? []).length})</Copy>
        <Button label="Manage debts" small secondary onPress={() => router.push('/debts' as Href)} />
      </View>
      {(state.debts ?? []).length === 0 ? (
        <Copy variant="small" muted>Compare Avalanche vs Snowball payoff and preview extra payments without changing your plan.</Copy>
      ) : (
        <Row
          label="Total recorded debt balance"
          value={money((state.debts ?? []).reduce((sum, d) => sum + d.balance_cents, 0))}
          bold
        />
      )}
    </Card>

    {state.summary.transaction_count > 0 && <Card>
      <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        <Copy variant="title">Imported transactions ({state.summary.transaction_count})</Copy>
        <Button label={showTxns ? 'Hide' : 'Show latest'} small secondary onPress={() => setShowTxns(!showTxns)} />
      </View>
      {showTxns && (txnsQuery.data?.transactions ?? []).map(t => (
        <Row key={t.id} label={`${t.date} · ${t.description.slice(0, 32)} (${t.category})`} value={money(t.amount)} />
      ))}
    </Card>}

    {state.actions.some(a => a.status !== 'planned') && <Card>
      <Copy variant="title">History</Copy>
      {state.actions.filter(a => a.status !== 'planned').map(a => (
        <Row key={a.id} label={`${a.status === 'completed' ? 'Completed' : 'Cancelled'} · ${a.completed_on ?? a.created_on}`} value={money(a.amount)} />
      ))}
    </Card>}
  </>;
}

export default function PlanScreen() {
  return <Screen title="My Plan" eyebrow="Vela"><StateGate>{state => <PlanContent state={state} />}</StateGate></Screen>;
}
