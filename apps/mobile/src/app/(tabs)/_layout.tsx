import React from 'react';
import { Tabs, Redirect, usePathname } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { request } from '../../lib/api';
import { PersonalView } from '../../lib/generated';
import { Feather } from '@expo/vector-icons';
import { useConnection } from '../../lib/state';
import { Loading } from '../../components/ui';
import { usePalette } from '../../theme';

export default function TabLayout() {
  const p = usePalette();
  const {ready, connected} = useConnection();
  const path = usePathname();
  const personal = useQuery({queryKey: ['personal'], queryFn: () => request<PersonalView>('/v2/personal'), enabled: connected});
  if (!ready) return <Loading />;
  if (!connected) return <Redirect href="/connect" />;
  if (personal.isPending) return <Loading />;
  if (personal.data?.data.planning?.active) {
    if (path === '/') return <Redirect href="/personal" />;
    if (path === '/plan') return <Redirect href="/shared-plan" />;
    if (path === '/assistant') return <Redirect href="/shared-assistant" />;
  }
  return <Tabs screenOptions={{headerShown: false, tabBarActiveTintColor: p.accent, tabBarInactiveTintColor: p.muted,
    tabBarStyle: {backgroundColor: p.background, borderTopColor: p.border}, tabBarLabelStyle: {fontFamily: 'Manrope_600SemiBold'}}}>
    <Tabs.Screen name="index" options={{title: 'Today', tabBarIcon: ({color, size}) => <Feather name="sun" color={typeof color === 'string' ? color : p.muted} size={size} />}} />
    <Tabs.Screen name="plan" options={{title: 'My Plan', tabBarIcon: ({color, size}) => <Feather name="flag" color={typeof color === 'string' ? color : p.muted} size={size} />}} />
    <Tabs.Screen name="assistant" options={{title: 'Assistant', tabBarIcon: ({color, size}) => <Feather name="message-square" color={typeof color === 'string' ? color : p.muted} size={size} />}} />
  </Tabs>;
}
