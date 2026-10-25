import React, { useEffect, useState } from 'react';
import { View } from 'react-native';
import { router } from 'expo-router';
import { Button, Card, Chip, Copy, Field, Loading, Notice, Screen } from '../components/ui';
import { useCommand, useFinancialState } from '../lib/state';
import { cents, localDate, money, Obligation, Snapshot } from '../lib/api';
import { space } from '../theme';

export default function SnapshotScreen() {
  const query = useFinancialState();
  const command = useCommand();
  const [nickname, setNickname] = useState('Sanatbek');
  const [cash, setCash] = useState('1000');
  const [buffer, setBuffer] = useState('100');
  const [goalName, setGoalName] = useState('Emergency reserve');
  const [goal, setGoal] = useState('1000');
  const [saved, setSaved] = useState('0');
  const [costs, setCosts] = useState<Obligation[]>([]);
  const [label, setLabel] = useState('');
  const [cost, setCost] = useState('');
  const [due, setDue] = useState(localDate(7));
  const [kind, setKind] = useState<Obligation['kind']>('other');
  const [horizon, setHorizon] = useState(() => localDate(30));
  const [complete, setComplete] = useState(true);
  const [debtKnown, setDebtKnown] = useState(true);
  const [error, setError] = useState('');
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (query.data && !initialized) {
      const s = query.data.snapshot;
      if (s) {
        setNickname(s.nickname);
        setCash(String(s.cash / 100));
        setBuffer(String(s.protected / 100));
        setSaved(String(s.saved / 100));
        setGoal(String(s.goal_target / 100));
        setGoalName(s.goal_name);
        setCosts(s.obligations);
        setHorizon(s.horizon);
        setComplete(s.obligations_complete);
        setDebtKnown(s.debt_known);
      }
      setInitialized(true);
    }
  }, [query.data, initialized]);

  function addCost() {
    try {
      if (!label.trim()) throw new Error('Enter a bill name.');
      const amount = cents(cost);
      if (!amount) throw new Error('Enter an amount above zero.');
      if (!/^\d{4}-\d{2}-\d{2}$/.test(due)) throw new Error('Use YYYY-MM-DD for the date.');
      setCosts([...costs, {id: `cost-${Date.now()}`, label: label.trim(), amount, due, kind}]);
      setLabel(''); setCost(''); setError('');
    } catch (e) { setError(e instanceof Error ? e.message : 'Check this bill.'); }
  }

  function save() {
    if (!query.data) return;
    try {
      const snapshot: Snapshot = {
        nickname: nickname.trim() || 'Alex', currency: 'EUR', as_of: localDate(), horizon,
        cash: cents(cash), protected: cents(buffer), saved: cents(saved), goal_target: cents(goal),
        goal_name: goalName.trim() || 'Emergency reserve', obligations: costs,
        obligations_complete: complete, debt_known: debtKnown, provenance: 'manual',
      };
      setError('');
      command.mutate({path: '/v1/snapshot', method: 'PUT', body: {revision: query.data.revision, snapshot}}, {onSuccess: () => router.replace('/')});
    } catch (e) { setError(e instanceof Error ? e.message : 'Check your numbers.'); }
  }

  const hasCompletedStep = query.data?.actions.some(a => a.status === 'completed') ?? false;

  return <Screen title="Balance & bills" eyebrow="Manual setup">
    {query.isPending ? <Loading /> : query.isError ? <Notice>{query.error.message}</Notice> : <>
      <Card>
        <Copy variant="title">1. Cash & buffer</Copy>
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}><Field label="Your name" value={nickname} onChangeText={setNickname} /></View>
          <View style={{flex: 1}}><Field label="Plan through (≤ 93d)" value={horizon} onChangeText={setHorizon} /></View>
        </View>
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}><Field label="Total cash (EUR)" numeric value={cash} onChangeText={setCash} /></View>
          <View style={{flex: 1}}><Field label="Safety buffer (EUR)" numeric value={buffer} onChangeText={setBuffer} /></View>
        </View>
      </Card>

      <Card>
        <Copy variant="title">2. Goal</Copy>
        <Field label="Goal name" value={goalName} onChangeText={setGoalName} />
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}><Field label="Target (EUR)" numeric value={goal} onChangeText={setGoal} /></View>
          <View style={{flex: 1}}><Field label={hasCompletedStep ? 'Set aside (locked)' : 'Already set aside'} numeric value={saved} onChangeText={hasCompletedStep ? () => {} : setSaved} /></View>
        </View>
      </Card>

      <Card>
        <Copy variant="title">3. Unpaid bills until {horizon}</Copy>
        {costs.map(o => (
          <Button key={o.id} small secondary label={`${o.label} · ${money(o.amount)} · ${o.due} (${o.kind})  ✕`}
            onPress={() => setCosts(costs.filter(c => c.id !== o.id))} />
        ))}
        <Field label="New bill name" placeholder="Rent, Electricity, Loan…" value={label} onChangeText={setLabel} />
        <View style={{flexDirection: 'row', gap: space.sm}}>
          <View style={{flex: 1}}><Field label="Amount (EUR)" numeric placeholder="250" value={cost} onChangeText={setCost} /></View>
          <View style={{flex: 1}}><Field label="Due (YYYY-MM-DD)" value={due} onChangeText={setDue} /></View>
        </View>
        <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
          {(['rent', 'living', 'debt', 'other'] as const).map(k => (
            <Chip key={k} label={k} active={kind === k} onPress={() => setKind(k)} />
          ))}
        </View>
        <Button label="+ Add bill to list" small secondary onPress={addCost} />
        <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs, paddingTop: space.xs}}>
          <Chip label={complete ? '✓ All bills included' : 'Bills incomplete'} active={complete} onPress={() => setComplete(!complete)} />
          <Chip label={debtKnown ? '✓ Debts checked' : 'Debts unchecked'} active={debtKnown} onPress={() => setDebtKnown(!debtKnown)} />
        </View>
      </Card>

      {(error || command.error) && <Notice>{error || command.error?.message}</Notice>}
      <Button label={command.isPending ? 'Saving…' : 'Save balance & bills'} disabled={command.isPending} onPress={save} />
    </>}
  </Screen>;
}
