import React, { useState } from 'react';
import { View } from 'react-native';
import { router } from 'expo-router';
import * as DocumentPicker from 'expo-document-picker';
import { useMutation } from '@tanstack/react-query';
import { Button, Card, Chip, Copy, Field, Notice, Row, Screen } from '../components/ui';
import { useCommand, useFinancialState } from '../lib/state';
import { cents, ImportPreview, money, uploadStatement } from '../lib/api';
import { space } from '../theme';

export default function ImportScreen() {
  const stateQuery = useFinancialState();
  const command = useCommand();
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [cashText, setCashText] = useState('');
  const [updateBalance, setUpdateBalance] = useState(true);
  const [selectedBills, setSelectedBills] = useState<string[]>([]);
  const [localError, setLocalError] = useState('');

  const upload = useMutation({
    mutationFn: uploadStatement,
    onSuccess: data => {
      setPreview(data);
      setSelectedBills(data.recurring.map(r => r.id));
      if (data.closing_balance !== null && data.closing_balance >= 0) {
        setCashText(String(data.closing_balance / 100));
        setUpdateBalance(true);
      } else if (stateQuery.data?.snapshot) {
        setCashText(String(stateQuery.data.snapshot.cash / 100));
        setUpdateBalance(false);
      } else {
        setCashText('');
        setUpdateBalance(true);
      }
      setLocalError('');
    },
  });

  async function pickFile() {
    try {
      setLocalError('');
      const result = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        copyToCacheDirectory: true,
      });
      if (result.canceled || !result.assets?.[0]) return;
      const asset = result.assets[0];
      upload.mutate({
        uri: asset.uri,
        name: asset.name,
        mimeType: asset.mimeType,
        file: (asset as {file?: File}).file,
        base64: asset.base64,
      });
    } catch (e) {
      setLocalError(e instanceof Error ? e.message : 'Could not pick file.');
    }
  }

  function toggleBill(id: string) {
    setSelectedBills(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  function apply() {
    if (!preview || !stateQuery.data) return;
    try {
      const needsBalance = !stateQuery.data.snapshot || updateBalance;
      const cash = needsBalance ? cents(cashText) : undefined;
      setLocalError('');
      command.mutate({
        path: `/v1/imports/${preview.id}/apply`,
        body: {revision: stateQuery.data.revision, cash, obligation_ids: selectedBills},
      }, {onSuccess: () => router.replace('/')});
    } catch (e) {
      setLocalError(e instanceof Error ? e.message : 'Enter a valid balance in EUR.');
    }
  }

  return <Screen title="Upload statement" eyebrow="CSV · Excel · PDF · Photo">
    <Card soft>
      <Copy variant="title">Import your real bank data</Copy>
      <Copy muted>CSV and Excel (.xlsx) files are parsed directly and categorized with Gemini. PDF statements and screenshots are read with Gemini 3.5 Flash-Lite.</Copy>
      <Button label={upload.isPending ? 'Reading statement…' : preview ? 'Pick a different file' : 'Choose file (CSV / XLSX / PDF / Image)'} disabled={upload.isPending} onPress={() => {void pickFile();}} />
    </Card>

    {(localError || upload.error || command.error) && (
      <Notice>{localError || upload.error?.message || command.error?.message}</Notice>
    )}

    {preview && <>
      <Card>
        <Copy variant="title">{preview.filename}</Copy>
        <Copy variant="small" muted>
          {preview.transactions.length} transactions · {preview.period_start} → {preview.period_end} · {preview.parser === 'gemini' ? `AI (${preview.model})` : preview.model ? `Local + ${preview.model}` : 'Local parser'}
        </Copy>
        <Row label="Total income" value={money(preview.income)} />
        <Row label="Total spending" value={money(preview.spending)} />
        {preview.closing_balance !== null && <Row label="Statement closing balance" value={money(preview.closing_balance)} />}
        {preview.warnings.map((w, i) => <Notice key={i}>{w}</Notice>)}
      </Card>

      <Card>
        <Copy variant="title">Balance setting</Copy>
        {stateQuery.data?.snapshot && (
          <View style={{flexDirection: 'row', gap: space.xs}}>
            <Chip label="Update current cash" active={updateBalance} onPress={() => setUpdateBalance(true)} />
            <Chip label={`Keep existing (${money(stateQuery.data.snapshot.cash)})`} active={!updateBalance} onPress={() => setUpdateBalance(false)} />
          </View>
        )}
        {(!stateQuery.data?.snapshot || updateBalance) && (
          <Field label="Current cash balance (EUR)" numeric placeholder="e.g. 2186.53" value={cashText} onChangeText={setCashText} />
        )}
      </Card>

      {preview.recurring.length > 0 && <Card>
        <Copy variant="title">Detected recurring bills ({preview.recurring.length})</Copy>
        <Copy variant="small" muted>Tap to toggle which upcoming bills to add to your plan:</Copy>
        <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
          {preview.recurring.map(r => (
            <Chip key={r.id} label={`${r.label.slice(0, 22)} · ${money(r.amount)} (${r.next_due})`}
              active={selectedBills.includes(r.id)} onPress={() => toggleBill(r.id)} />
          ))}
        </View>
      </Card>}

      <Card>
        <Copy variant="title">Sample transactions ({Math.min(10, preview.transactions.length)} of {preview.transactions.length})</Copy>
        {preview.transactions.slice(0, 10).map(t => (
          <Row key={t.id} label={`${t.date} · ${t.description.slice(0, 28)} (${t.category})`} value={money(t.amount)} />
        ))}
      </Card>

      <Button label={command.isPending ? 'Applying…' : 'Save imported data'} disabled={command.isPending} onPress={apply} />
    </>}
  </Screen>;
}
