import React, { useRef, useState } from 'react';
import { router } from 'expo-router';
import * as DocumentPicker from 'expo-document-picker';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Copy, Notice, Row, Screen } from '../components/ui';
import { useFinancialState } from '../lib/state';
import { ImportPreview, money, request, uploadStatement } from '../lib/api';

export default function ImportScreen() {
  const state = useFinancialState();
  const cache = useQueryClient();
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [page, setPage] = useState(0);
  const [error, setError] = useState('');
  const retry = useRef<{signature: string; key: string} | null>(null);
  const upload = useMutation({mutationFn: uploadStatement, onSuccess: data => {setPreview(data); setPage(0); setError('');}});
  const apply = useMutation({
    mutationFn: async () => {
      if (!preview || !state.data) throw new Error('Refresh your data before saving.');
      const signature = `${preview.id}:${state.data.revision}`;
      if (retry.current?.signature !== signature) retry.current = {signature, key: `analytics-${Date.now()}-${Math.random().toString(36).slice(2)}`};
      return request(`/v2/imports/${preview.id}/apply`, 'POST', {revision: state.data.revision}, retry.current.key);
    },
    onSuccess: () => {void cache.invalidateQueries(); router.replace('/observations');},
  });
  async function pick() {
    try {
      setError('');
      const result = await DocumentPicker.getDocumentAsync({type: '*/*', copyToCacheDirectory: true});
      if (result.canceled || !result.assets?.[0]) return;
      const asset = result.assets[0];
      setPreview(null); apply.reset();
      upload.mutate({uri: asset.uri, name: asset.name, mimeType: asset.mimeType, file: (asset as {file?: File}).file, base64: asset.base64});
    } catch (e) {setError(e instanceof Error ? e.message : 'Could not select a file.');}
  }
  const busy = upload.isPending || apply.isPending;
  return <Screen title="Statement analysis" eyebrow="Historical records · EUR">
    <Notice>Statements are used for analysis only. Saving never changes balances, savings, bills, debt or completed steps. A statement closing balance is historical evidence.</Notice>
    <Copy muted>CSV and Excel are read locally. If AI processing is enabled on your server, document reading or category suggestions may use the configured external provider. Upload synthetic data for this local test.</Copy>
    <Button label={upload.isPending ? 'Reading statement…' : preview ? 'Pick a different file' : 'Choose file (CSV / XLSX / PDF / Image)'} disabled={busy} onPress={() => {void pick();}} />
    {Boolean(error || upload.error || apply.error || state.error) && <Notice>{error || upload.error?.message || apply.error?.message || state.error?.message}</Notice>}
    {(apply.isError || state.isError) && <Button label="Refresh and try again" secondary onPress={() => {void state.refetch(); apply.reset();}} />}
    {preview && <>
      <Card>
        <Copy variant="title">{preview.filename}</Copy>
        <Copy muted>{preview.transactions.length} transactions · {preview.period_start} → {preview.period_end} · {preview.currency} · {preview.parser === 'local' ? 'Local parser' : 'AI parser'}</Copy>
        {preview.currency !== 'EUR' ? <Notice>Only EUR analysis is supported on this path. No conversion was applied; this statement cannot be saved here.</Notice> : <>
          <Row label="Income (excluding labelled refunds)" value={money(preview.income)} />
          <Row label="Recorded spending" value={money(preview.spending)} />
          <Row label="Refund credits (labelled)" value={money(preview.refunds ?? 0)} />
          <Row label="Spending less refund credits" value={money(preview.net_spending ?? preview.spending)} />
          {preview.closing_balance !== null && <Row label="Historical closing balance · not applied" value={money(preview.closing_balance)} />}
        </>}
        {preview.warnings.map((warning, i) => <Notice key={i}>{warning}</Notice>)}
        <Copy muted>Categories and refund labels are suggestions based on descriptions. They do not confirm account ownership or a matched purchase.</Copy>
      </Card>
      <Card>
        <Copy variant="title">Review transactions · page {page + 1} of {Math.max(1, Math.ceil(preview.transactions.length / 20))}</Copy>
        {preview.transactions.slice(page * 20, page * 20 + 20).map(t => <Row key={t.id} label={`${t.date} · ${t.description} (${t.category})`} value={preview.currency === 'EUR' ? money(t.amount) : `${t.amount} minor units · ${preview.currency}`} />)}
        <Button label="Previous rows" secondary disabled={page === 0 || busy} onPress={() => setPage(page - 1)} />
        <Button label="Next rows" secondary disabled={(page + 1) * 20 >= preview.transactions.length || busy} onPress={() => setPage(page + 1)} />
      </Card>
      <Button label="Save statement analysis" loading={apply.isPending} disabled={upload.isPending || !state.data || preview.currency !== 'EUR'} onPress={() => apply.mutate()} />
    </>}
    <Button label="Your saved accounts" secondary disabled={busy} onPress={() => router.push('/personal')} />
  </Screen>;
}
