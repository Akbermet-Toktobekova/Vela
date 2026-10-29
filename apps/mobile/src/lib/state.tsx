import React, { createContext, useContext, useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { FinancialState, request, restoreConnection } from './api';

const client = new QueryClient({defaultOptions: {queries: {retry: false, staleTime: 0}, mutations: {retry: false}}});
const ConnectionContext = createContext({ready: false, connected: false, setConnected: (_value: boolean) => {}});
export function Providers({children}: React.PropsWithChildren) {
  const [ready, setReady] = useState(false);
  const [connected, setConnected] = useState(false);
  useEffect(() => { restoreConnection().then(setConnected).catch(() => setConnected(false)).finally(() => setReady(true)); }, []);
  return <QueryClientProvider client={client}><ConnectionContext.Provider value={{ready, connected, setConnected}}>{children}</ConnectionContext.Provider></QueryClientProvider>;
}
export const useConnection = () => useContext(ConnectionContext);
export function useFinancialState() {
  const {connected} = useConnection();
  return useQuery({queryKey: ['state'], queryFn: () => request<FinancialState>('/v1/state'), enabled: connected});
}
export function useCommand() {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: ({path, body, method = 'POST'}: {path: string; body?: unknown; method?: string}) =>
      request<FinancialState>(path, method, body, `mobile-${Date.now()}-${Math.random().toString(36).slice(2)}`),
    onSuccess: () => cache.invalidateQueries(),
    onError: () => cache.invalidateQueries(),
  });
}
