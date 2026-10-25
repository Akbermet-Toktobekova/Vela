import React, { useState } from 'react';
import { TextInput, View } from 'react-native';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Chip, Copy, Notice, Screen } from '../../components/ui';
import { StateGate } from '../../components/StateGate';
import { AIStatus, ChatMessage, ChatReply, FinancialState, money, request } from '../../lib/api';
import { radius, space, type, usePalette } from '../../theme';

const PROMPTS = [
  'How much can I safely save right now?',
  'Explain my cash breakdown and unpaid bills.',
  'Where did my money go in my imported statement?',
  'How can I reach my emergency goal faster?',
];

function AssistantContent({state}: {state: FinancialState}) {
  const p = usePalette();
  const cache = useQueryClient();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [lastModel, setLastModel] = useState<string | null>(null);

  const statusQuery = useQuery({
    queryKey: ['ai-status'],
    queryFn: () => request<AIStatus>('/v1/ai/status'),
  });

  const chatMutation = useMutation({
    mutationFn: (history: ChatMessage[]) => request<ChatReply>('/v1/chat', 'POST', {messages: history}),
    onSuccess: (res, history) => {
      setMessages([...history, {role: 'assistant', content: res.reply}]);
      setLastModel(res.model ?? res.source);
      void cache.invalidateQueries({queryKey: ['ai-status']});
    },
  });

  function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || chatMutation.isPending) return;
    const next: ChatMessage[] = [...messages, {role: 'user', content: trimmed}];
    setMessages(next);
    setInput('');
    chatMutation.mutate(next);
  }

  const s = state.snapshot!;
  return <>
    <Card soft>
      <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
        <Copy variant="small" muted>Free to plan: {money(state.available)} · Goal: {money(s.saved)} / {money(s.goal_target)}</Copy>
        {lastModel && <Copy variant="small" muted>{lastModel}</Copy>}
      </View>
      <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
        {PROMPTS.map(prompt => (
          <Chip key={prompt} label={prompt} onPress={() => send(prompt)} />
        ))}
      </View>
    </Card>

    {messages.length === 0 && (
      <Card>
        <Copy variant="title">Ask Vela anything about your finances</Copy>
        <Copy muted>Vela uses Gemini 3.1 & 3.5 Flash-Lite grounded in your exact cash ({money(s.cash)}), bills ({money(state.breakdown.bills)}), and imported transactions ({state.summary.transaction_count}).</Copy>
      </Card>
    )}

    {messages.map((m, idx) => (
      <View key={idx} style={{
        alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
        maxWidth: '90%',
        backgroundColor: m.role === 'user' ? p.accent : p.surface,
        borderColor: m.role === 'user' ? p.accent : p.border,
        borderWidth: 1,
        borderRadius: radius.card,
        padding: space.md,
      }}>
        <Copy color={m.role === 'user' ? p.accentText : p.text}>{m.content}</Copy>
      </View>
    ))}

    {chatMutation.isPending && <Copy variant="small" muted>Thinking with Gemini Flash-Lite…</Copy>}
    {chatMutation.error && <Notice>{chatMutation.error.message}</Notice>}

    <Card>
      <View style={{flexDirection: 'row', gap: space.sm, alignItems: 'center'}}>
        <TextInput
          accessibilityLabel="Ask a question"
          placeholder="Ask about your balance, bills, or spending…"
          placeholderTextColor={p.muted}
          value={input}
          onChangeText={setInput}
          onSubmitEditing={() => send(input)}
          style={{
            flex: 1, minHeight: 40, borderWidth: 1, borderColor: p.border, backgroundColor: p.background,
            borderRadius: radius.button, paddingHorizontal: space.md, paddingVertical: 8, color: p.text,
            fontFamily: 'Manrope_400Regular', fontSize: type.body,
          }}
        />
        <Button label="Send" small disabled={!input.trim() || chatMutation.isPending} onPress={() => send(input)} />
      </View>
      {messages.length > 0 && <Button label="Clear chat" small secondary onPress={() => setMessages([])} />}
    </Card>

    {statusQuery.data && (
      <Card>
        <Copy variant="small" muted>
          AI quota today: {statusQuery.data.models.map(m => `${m.model.replace('gemini-', '')}: ${m.requests_today}/${m.daily_limit}`).join(' · ')}
        </Copy>
      </Card>
    )}
  </>;
}

export default function AssistantScreen() {
  return <Screen title="Assistant" eyebrow="Vela AI"><StateGate>{state => <AssistantContent state={state} />}</StateGate></Screen>;
}
