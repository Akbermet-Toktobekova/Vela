import React from 'react';
import { Redirect, Stack, usePathname } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useFonts, Manrope_400Regular, Manrope_600SemiBold } from '@expo-google-fonts/manrope';
import { Providers, useConnection } from '../lib/state';
import { connectionRedirect } from '../lib/navigation';
import { Loading } from '../components/ui';
import { usePalette } from '../theme';

export default function RootLayout() {
  const [loaded, error] = useFonts({Manrope_400Regular, Manrope_600SemiBold});
  if (!loaded && !error) return <Loading />;
  return <Providers><ConnectedStack /></Providers>;
}

function ConnectedStack() {
  const p = usePalette();
  const path = usePathname();
  const {ready, connected} = useConnection();
  if (!ready) return <Loading />;
  if (!connected && !['/connect', '/pilot', '/_sitemap'].includes(path)) return <Redirect href={connectionRedirect(path)} />;
  return <><StatusBar style="auto" /><Stack screenOptions={{headerStyle: {backgroundColor: p.background}, headerTintColor: p.text, contentStyle: {backgroundColor: p.background}}}>
    <Stack.Screen name="(tabs)" options={{headerShown: false}} />
    <Stack.Screen name="pilot" options={{headerShown: false}} />
    <Stack.Screen name="personal" options={{headerShown: false}} />
    <Stack.Screen name="shared-plan" options={{headerShown: false}} />
    <Stack.Screen name="shared-assistant" options={{headerShown: false}} />
    <Stack.Screen name="connect" options={{title: 'Connect API'}} />
    <Stack.Screen name="snapshot" options={{title: 'Balance & bills'}} />
    <Stack.Screen name="import" options={{title: 'Import statement'}} />
    <Stack.Screen name="adjust" options={{title: 'Choose amount'}} />
    <Stack.Screen name="settings" options={{title: 'Data & AI'}} />
  </Stack></>;
}
