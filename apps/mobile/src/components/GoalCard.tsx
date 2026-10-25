import React from 'react';
import { View } from 'react-native';
import { FinancialState, money } from '../lib/api';
import { usePalette, radius, space } from '../theme';
import { Card, Copy } from './ui';

export function GoalCard({state}: {state: FinancialState}) {
  const p = usePalette();
  const s = state.snapshot!;
  const percentage = Math.min(100, Math.floor(s.saved / s.goal_target * 100));
  return <Card>
    <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', gap: space.sm}}>
      <Copy variant="title">{s.goal_name}</Copy>
      <Copy variant="small" muted>{percentage}% · {money(Math.max(0, s.goal_target - s.saved))} left</Copy>
    </View>
    <View style={{flexDirection: 'row', alignItems: 'baseline', gap: space.xs}}>
      <Copy variant="money">{money(s.saved)}</Copy>
      <Copy variant="small" muted>of {money(s.goal_target)}</Copy>
    </View>
    <View accessibilityRole="progressbar" accessibilityLabel="Goal progress" accessibilityValue={{min: 0, max: 100, now: percentage}} style={{height: 6, backgroundColor: p.soft, borderRadius: radius.sm, overflow: 'hidden'}}>
      <View style={{height: 6, width: `${percentage}%`, backgroundColor: p.accent}} />
    </View>
  </Card>;
}
