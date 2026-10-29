import React, { useState } from 'react';
import { router } from 'expo-router';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { useMutation } from '@tanstack/react-query';
import { Button, Card, Copy, Field, Notice, Screen } from '../components/ui';
import { connect } from '../lib/api';
import { useConnection } from '../lib/state';

function defaultApiUrl(): string {
  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) {
    const host = hostUri.split(':')[0];
    if (host) return `http://${host}:8000`;
  }
  return Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';
}

export default function ConnectScreen() {
  const [url, setUrl] = useState(defaultApiUrl);
  const [token, setToken] = useState('');
  const {setConnected} = useConnection();
  const mutation = useMutation({mutationFn: () => connect({url, token}), onSuccess: () => {setConnected(true); router.replace('/personal');}});
  return <Screen title="Connect Vela" eyebrow="Local API">
    <Card soft><Copy variant="title">Explore the new Vela experience</Copy><Copy muted>Try the first-time journey and new screens using isolated example data.</Copy><Button label="Open design preview" onPress={() => router.push("/pilot")} /></Card>
    <Card soft>
      <Copy variant="title">Personal finance & AI assistant</Copy>
      <Copy muted>Upload bank statements (CSV, XLSX, PDF, image), track bills and goals, and chat with Gemini 3.1 & 3.5 Flash-Lite.</Copy>
    </Card>
    <Card>
      <Field label="API address" value={url} onChangeText={setUrl} />
      <Field label="Access token (DEMO_API_TOKEN)" value={token} onChangeText={setToken} secure />
      {mutation.error && <Notice>{mutation.error.message}</Notice>}
      <Button label={mutation.isPending ? 'Connecting…' : 'Open Vela'} disabled={mutation.isPending || token.trim().length < 24} onPress={() => mutation.mutate()} />
    </Card>
  </Screen>;
}
