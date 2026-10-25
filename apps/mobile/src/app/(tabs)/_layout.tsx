import React from 'react';
import { Tabs, Redirect } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useConnection } from '../../lib/state';
import { Loading } from '../../components/ui';
import { usePalette } from '../../theme';

export default function TabLayout() {
  const p = usePalette();
  const {ready, connected} = useConnection();
  if (!ready) return <Loading />;
  if (!connected) return <Redirect href="/connect" />;
  return <Tabs screenOptions={{headerShown: false, tabBarActiveTintColor: p.accent, tabBarInactiveTintColor: p.muted,
    tabBarStyle: {backgroundColor: p.background, borderTopColor: p.border}, tabBarLabelStyle: {fontFamily: 'Manrope_600SemiBold'}}}>
    <Tabs.Screen name="index" options={{title: 'Today', tabBarIcon: ({color, size}) => <Feather name="sun" color={typeof color === 'string' ? color : p.muted} size={size} />}} />
    <Tabs.Screen name="plan" options={{title: 'My Plan', tabBarIcon: ({color, size}) => <Feather name="flag" color={typeof color === 'string' ? color : p.muted} size={size} />}} />
    <Tabs.Screen name="assistant" options={{title: 'Assistant', tabBarIcon: ({color, size}) => <Feather name="message-square" color={typeof color === 'string' ? color : p.muted} size={size} />}} />
  </Tabs>;
}
