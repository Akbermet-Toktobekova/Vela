import React from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useFonts, Manrope_400Regular, Manrope_600SemiBold } from '@expo-google-fonts/manrope';
import { Providers } from '../lib/state';
import { Loading } from '../components/ui';
import { usePalette } from '../theme';

export default function RootLayout() {
  const [loaded, error] = useFonts({Manrope_400Regular, Manrope_600SemiBold});
  const p = usePalette();
  if (!loaded && !error) return <Loading />;
  return <Providers><StatusBar style="auto" /><Stack screenOptions={{headerStyle: {backgroundColor: p.background}, headerTintColor: p.text, contentStyle: {backgroundColor: p.background}}}>
    <Stack.Screen name="(tabs)" options={{headerShown: false}} />
    <Stack.Screen name="connect" options={{title: 'Connect API'}} />
    <Stack.Screen name="snapshot" options={{title: 'Balance & bills'}} />
    <Stack.Screen name="import" options={{title: 'Import statement'}} />
    <Stack.Screen name="adjust" options={{title: 'Choose amount'}} />
    <Stack.Screen name="settings" options={{title: 'Data & AI'}} />
  </Stack></Providers>;
}
