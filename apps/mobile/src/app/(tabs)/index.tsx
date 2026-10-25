import React from 'react';
import { View } from 'react-native';
import { router } from 'expo-router';
import { Button, Card, Copy, Notice, Row, Screen } from '../../components/ui';
import { StateGate } from '../../components/StateGate';
import { GoalCard } from '../../components/GoalCard';
import { useCommand } from '../../lib/state';
import { FinancialState, money } from '../../lib/api';
import { space } from '../../theme';

function TodayContent({state}: {state: FinancialState}) {
  const command = useCommand();
  const s = state.snapshot!;
  const r = state.recommendation;
  const b = state.breakdown;
  const sum = state.summary;

  return <>
    <Card soft>
      <Copy variant="small" muted>Next step · checked {s.as_of}</Copy>
      <Copy variant="title">
        {r.kind === 'save' ? `Set aside ${money(r.amount)} for ${s.goal_name}`
          : r.kind === 'shortfall' ? 'Keep your money available'
          : r.kind === 'clarify' ? 'Quick check before planning'
          : r.kind === 'goal_reached' ? 'Goal reached'
          : 'Your plan is up to date'}
      </Copy>
      <Copy muted>{r.message}</Copy>

      {r.kind === 'save' && <>
        <Row label="Goal after this step" value={`${money(s.saved)} → ${money(s.saved + r.amount)}`} />
        <Row label="Free after this step" value={money(state.available - r.amount)} />
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}><Button label="Add to plan" disabled={command.isPending} onPress={() => command.mutate({path: '/v1/actions', body: {revision: state.revision, amount: r.amount}}, {onSuccess: () => router.push('/plan')})} /></View>
          <View style={{flex: 1}}><Button label="Change amount" secondary onPress={() => router.push('/adjust')} /></View>
        </View>
        <Button label="Skip for now" small secondary disabled={command.isPending} onPress={() => command.mutate({path: '/v1/defer', body: {revision: state.revision}})} />
      </>}

      {r.kind === 'clarify' && r.clarify_field && r.clarify_field !== 'refresh' && <>
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}>
            <Button label="Yes, all included" disabled={command.isPending}
              onPress={() => command.mutate({path: '/v1/confirm', body: {revision: state.revision, field: r.clarify_field}})} />
          </View>
          <View style={{flex: 1}}>
            <Button label="Add a bill" secondary onPress={() => router.push('/plan')} />
          </View>
        </View>
      </>}

      {r.kind === 'clarify' && r.clarify_field === 'refresh' && (
        <Button label="Update balance" onPress={() => router.push('/snapshot')} />
      )}

      {(r.kind === 'maintain' || r.kind === 'shortfall' || r.kind === 'goal_reached') && (
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}><Button label="Open My Plan" secondary onPress={() => router.push('/plan')} /></View>
          <View style={{flex: 1}}><Button label="Choose amount" secondary onPress={() => router.push('/adjust')} /></View>
        </View>
      )}
      {command.error && <Notice>{command.error.message}</Notice>}
    </Card>

    <Card>
      <Copy variant="title">How your cash breaks down</Copy>
      <Row label="Total cash" value={money(b.cash)} />
      <Row label="− Set aside for goal" value={money(b.saved)} />
      <Row label="− Protected buffer" value={money(b.protected)} />
      <Row label={`− Unpaid bills (${s.obligations.length})`} value={money(b.bills)} />
      {b.planned > 0 && <Row label="− Planned step" value={money(b.planned)} />}
      <Row label={`= Free until ${s.horizon}`} value={money(state.available)} bold />
    </Card>

    <GoalCard state={state} />

    {sum.transaction_count > 0 && <Card>
      <Copy variant="title">Statement summary ({sum.transaction_count} rows)</Copy>
      <Row label={`Income (${sum.period_start} → ${sum.period_end})`} value={money(sum.income)} />
      <Row label="Spending (last 30 days)" value={money(sum.spending)} />
      {sum.top_categories.slice(0, 4).map(c => <Row key={c.category} label={`  · ${c.category}`} value={money(c.amount)} />)}
    </Card>}

    <View style={{flexDirection: 'row', gap: space.sm}}>
      <View style={{flex: 1}}><Button label="Upload statement" onPress={() => router.push('/import')} /></View>
      <View style={{flex: 1}}><Button label="Edit balance" secondary onPress={() => router.push('/snapshot')} /></View>
    </View>
    <Button label="Data, AI quota & connection" small secondary onPress={() => router.push('/settings')} />
  </>;
}

export default function TodayScreen() {
  return <Screen title="Today" eyebrow="Vela"><StateGate>{state => <TodayContent state={state} />}</StateGate></Screen>;
}
