import React, { useState } from 'react';
import { Platform, Share, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Copy, Notice, Row, Screen } from '../components/ui';
import { AIStatus, disconnect, request } from '../lib/api';
import { useConnection } from '../lib/state';
import { space } from '../theme';

export default function SettingsScreen() {
  const [confirm, setConfirm] = useState(false);
  const [status, setStatus] = useState('');
  const cache = useQueryClient();
  const {setConnected} = useConnection();

  const aiQuery = useQuery({
    queryKey: ['ai-status'],
    queryFn: () => request<AIStatus>('/v1/ai/status'),
  });

  const mutation = useMutation({
    mutationFn: async (action: 'export' | 'delete' | 'disconnect') => {
      if (action === 'export') {
        const data = await request('/v1/export');
        const message = JSON.stringify(data, null, 2);
        if (Platform.OS === 'web') {
          const url = URL.createObjectURL(new Blob([message], {type: 'application/json'}));
          const link = document.createElement('a');
          link.href = url;
          link.download = 'vela-export.json';
          document.body.appendChild(link);
          try {link.click();} finally {link.remove(); setTimeout(() => URL.revokeObjectURL(url), 30_000);}
          setStatus('Export prepared. Your browser handles the download.');
        } else {
          await Share.share({message, title: 'Vela export'});
        }
      }
      if (action === 'delete') {
        await request('/v1/data', 'DELETE');
        cache.clear();
        setConfirm(false);
        setStatus('All balances, bills, plans and imported transactions deleted.');
      }
      if (action === 'disconnect') {
        await disconnect();
        cache.clear();
        setConnected(false);
        router.replace('/connect');
      }
    },
  });

  return <Screen title="Data & AI" eyebrow="Settings">
    <Button label="Your saved accounts" secondary onPress={() => router.push('/personal')} />
    <Copy muted>Export and deletion cover both saved accounts and the planning workspace.</Copy>
    {aiQuery.data && (
      <Card>
        <Copy variant="title">Gemini Flash-Lite status</Copy>
        <Row label="AI enabled" value={aiQuery.data.enabled ? 'Yes' : 'Disabled'} />
        <Row label="Chat model" value={aiQuery.data.routes.chat ?? 'gemini-3.1-flash-lite'} />
        <Row label="Document & category model" value={aiQuery.data.routes.document ?? 'gemini-3.5-flash-lite'} />
        {aiQuery.data.models.map(m => (
          <Row key={m.model} label={`${m.model} (today / 1m)`}
            value={`${m.requests_today}/${m.daily_limit} · ${m.requests_last_minute} rpm${m.cooling_down ? ' (cooling)' : ''}`} />
        ))}
      </Card>
    )}

    <Card>
      <Copy variant="title">Your data</Copy>
      <Copy muted>Data is stored in your local SQLite database. You can export it as JSON or wipe it anytime.</Copy>
      <View style={{flexDirection: 'row', gap: space.sm}}>
        <View style={{flex: 1}}><Button label="Upload statement" small onPress={() => router.push('/import')} /></View>
        <View style={{flex: 1}}><Button label="Export JSON" small secondary disabled={mutation.isPending} onPress={() => mutation.mutate('export')} /></View>
      </View>
      {confirm ? (
        <View style={{gap: space.xs}}>
          <Notice>Delete all balances, bills, plans and imported transactions?</Notice>
          <View style={{flexDirection: 'row', gap: space.sm}}>
            <View style={{flex: 1}}><Button label="Yes, delete all" small disabled={mutation.isPending} onPress={() => mutation.mutate('delete')} /></View>
            <View style={{flex: 1}}><Button label="Cancel" small secondary onPress={() => setConfirm(false)} /></View>
          </View>
        </View>
      ) : (
        <Button label="Delete all data" small secondary onPress={() => setConfirm(true)} />
      )}
      <Button label="Disconnect device" small secondary disabled={mutation.isPending} onPress={() => mutation.mutate('disconnect')} />
    </Card>

    {!!status && <Notice>{status}</Notice>}
    {mutation.error && <Notice>{mutation.error.message}</Notice>}
  </Screen>;
}
