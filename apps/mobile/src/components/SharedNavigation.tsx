import React from 'react';
import { View } from 'react-native';
import { router } from 'expo-router';
import { Chip } from './ui';

export function SharedNavigation({current}: {current: 'today' | 'plan' | 'assistant'}) {
  return <View accessibilityRole="tablist" style={{flexDirection: 'row', flexWrap: 'wrap', gap: 8}}>
    <Chip label="Today" active={current === 'today'} onPress={() => router.replace('/personal')} />
    <Chip label="My Plan" active={current === 'plan'} onPress={() => router.replace('/shared-plan')} />
    <Chip label="Assistant" active={current === 'assistant'} onPress={() => router.replace('/shared-assistant')} />
  </View>;
}
