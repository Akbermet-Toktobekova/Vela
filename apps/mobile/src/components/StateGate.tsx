import React from 'react';
import { Redirect, router } from 'expo-router';
import { FinancialState } from '../lib/api';
import { useCommand, useConnection, useFinancialState } from '../lib/state';
import { Button, Card, Copy, Loading, Notice } from './ui';

export function StateGate({children, allowEmpty = false}: {children: (state: FinancialState) => React.ReactNode; allowEmpty?: boolean}) {
  const query = useFinancialState();
  const command = useCommand();
  const {ready, connected} = useConnection();
  if (!ready) return <Loading />;
  if (!connected) return <Redirect href="/connect" />;
  if (query.isPending) return <Loading />;
  if (query.isError) return <><Notice>{query.error.message}</Notice><Button label="Try again" onPress={() => {void query.refetch();}} /><Button label="Connection settings" secondary onPress={() => router.push('/connect')} /></>;
  if (!query.data.snapshot && !allowEmpty) return <Card soft>
    <Copy variant="title">Start with your numbers</Copy>
    <Copy muted>Upload a bank statement (CSV, Excel, PDF or photo), enter your balance manually, or try a pre-built example.</Copy>
    <Button label="Upload statement (CSV / PDF)" onPress={() => router.push('/import')} />
    <Button label="Enter balance manually" secondary onPress={() => router.push('/snapshot')} />
    <Button label="Load example data" secondary disabled={command.isPending} onPress={() => command.mutate({path: '/v1/demo', body: {revision: query.data.revision}})} />
    {command.error && <Notice>{command.error.message}</Notice>}
  </Card>;
  return <>{children(query.data)}</>;
}
