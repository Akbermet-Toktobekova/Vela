import React, { useEffect, useState } from 'react';
import { BackHandler, View } from 'react-native';
import { router } from 'expo-router';
import { Button, Card, Chip, Copy, Field, IconButton, Notice, Row, Screen } from '../components/ui';
import { space } from '../theme';

type Page = 'welcome' | 'intent' | 'account' | 'income-profile' | 'today' | 'plan' | 'assistant' | 'income' | 'balance' | 'import' | 'reminders' | 'settings' | 'evidence';
type Scenario = 'ready' | 'empty' | 'offline' | 'stale' | 'conflict' | 'unavailable';
const tabs: {page: Page; label: string}[] = [{page: 'today', label: 'Today'}, {page: 'plan', label: 'My Plan'}, {page: 'assistant', label: 'Assistant'}];
const choices = ['Understand my spending', 'Build a financial cushion', 'Manage debt', 'Save for something', 'Not sure yet'];
const format = (amount: number) => new Intl.NumberFormat('en-IE', {style: 'currency', currency: 'EUR'}).format(amount / 100);
function amount(text: string): number | null {
  if (!/^\d+(?:[.,]\d{1,2})?$/.test(text.trim())) return null;
  const [whole, decimal = ''] = text.trim().replace(',', '.').split('.');
  const value = Number(whole) * 100 + Number(decimal.padEnd(2, '0'));
  return Number.isSafeInteger(value) ? value : null;
}

/** Deliberately local, synthetic prototype. No API calls or personal-state commands. */
export default function PilotScreen() {
  const [history, setHistory] = useState<Page[]>(['welcome']);
  const page: Page = history[history.length - 1] ?? 'welcome';
  const [balance, setBalance] = useState<number | null>(null);
  const [intent, setIntent] = useState('Not sure yet');
  const [incomeType, setIncomeType] = useState('Not sure yet');
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [scenario, setScenario] = useState<Scenario>('ready');
  const [included, setIncluded] = useState<'add' | 'included' | 'replace' | null>(null);
  const [replacement, setReplacement] = useState('');
  const [action, setAction] = useState<'none' | 'planned' | 'completed'>('none');
  const [explanation, setExplanation] = useState(false);
  const [chat, setChat] = useState<{question: string; answer: string}[]>([]);
  const [importStage, setImportStage] = useState<'choose' | 'reading' | 'review' | 'saved' | 'error'>('choose');
  const [reminders, setReminders] = useState(false);
  const [frequency, setFrequency] = useState('Weekly');
  const [time, setTime] = useState('18:00');
  const [weekday, setWeekday] = useState('Monday');
  const [interval, setInterval] = useState('3');
  const [reminderSaved, setReminderSaved] = useState(false);
  const [subscription, setSubscription] = useState<'suggested' | 'confirmed' | 'rejected'>('suggested');
  const go = (next: Page) => { setError(''); setInput(''); setHistory(h => [...h, next]); };
  const back = () => { setError(''); setInput(''); setHistory(h => h.length > 1 ? h.slice(0, -1) : h); };
  useEffect(() => {
    const handler = BackHandler.addEventListener('hardwareBackPress', () => {
      if (history.length <= 1) return false;
      setHistory(h => h.slice(0, -1)); return true;
    });
    return () => handler.remove();
  }, [history.length]);
  useEffect(() => {
    if (importStage !== 'reading') return;
    const timer = setTimeout(() => setImportStage('review'), 650);
    return () => clearTimeout(timer);
  }, [importStage]);
  const blocked = scenario === 'offline' || scenario === 'conflict';
  const saveMoney = () => {
    if (blocked) { setError(scenario === 'offline' ? 'You are offline. Your entry is still here. Try again when connected.' : 'The balance changed elsewhere. Review the latest balance before saving.'); return; }
    const parsed = amount(input);
    if (parsed === null || (page === 'income' && parsed === 0)) { setError('Enter a valid amount with up to two decimal places.'); return; }
    if (page === 'income') {
      if (!included) { setError('Choose whether this income is already in your balance.'); return; }
      if (included === 'replace') {
        const latest = amount(replacement);
        if (latest === null) { setError('Enter your current balance.'); return; }
        setBalance(latest);
      } else if (included === 'add') {
        if (balance === null) { setError('Your balance is unknown. Choose Enter current balance instead.'); return; }
        if (!Number.isSafeInteger(balance + parsed)) { setError('This amount is too large.'); return; }
        setBalance(balance + parsed);
      }
    } else setBalance(parsed);
    setScenario('ready'); go(page === 'account' ? 'income-profile' : 'today');
  };
  const ask = (question: string) => {
    const answer = scenario === 'unavailable' ? 'The assistant is unavailable. Your saved information is still accessible. Try again later.'
      : question.toLowerCase().includes('spend') || question.toLowerCase().includes('recurring')
      ? 'Example analysis: three payments of €12.99 to Example Streaming across July–September suggest a recurring payment. This does not tell us whether you use the service. Review the evidence before adding an action.'
      : question.toLowerCase().includes('smaller') || question.toLowerCase().includes('what if')
      ? 'You can review one service at a time. This conversation does not change your money or plan.'
      : 'Recommendation example-subscriptions-v1: checking a recurring service helps you decide whether to keep it. The example shows three monthly payments. Cancelling is your choice; potential future savings are not money received. Your balance has not changed.';
    setChat(c => [...c, {question, answer}]); setInput('');
  };
  const titles: Record<Page, string> = {welcome: 'Welcome to Vela', intent: 'Start with what matters', account: 'Your money', 'income-profile': 'Your income', today: 'Today', plan: 'My Plan', assistant: 'Assistant', income: 'Add income', balance: 'Update balance', import: 'Statement analysis', reminders: 'Your reminders', settings: 'Profile & data', evidence: 'Supporting transactions'};
  const moneyFields = <>
    <Copy muted>Main account · EUR · example session</Copy>
    <Copy>Last known balance: {balance === null ? 'Not provided' : format(balance)}</Copy>
    <Field label={page === 'income' ? 'Income received (EUR)' : 'Current balance (EUR)'} numeric value={input} onChangeText={v => {setInput(v); setError('');}} placeholder="0.00" error={error || undefined} />
  </>;
  return <Screen title={titles[page]} eyebrow="Vela · design preview">
    <Notice>Synthetic preview only. Changes stay in this screen session. No account, email, file upload, AI or notification is sent.</Notice>
    <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.sm}}>
      {history.length > 1 && <Button small secondary label="Back" onPress={back} />}
      <Button small secondary label="Exit preview" onPress={() => router.canGoBack() ? router.back() : router.replace('/connect')} />
    </View>
    {page === 'welcome' && <Card soft>
      <Copy variant="hero">Understand your money. Choose your next step.</Copy>
      <Copy muted>Start with what you know. Build your picture over time.</Copy>
      <Button label="Try the first-time journey" onPress={() => go('intent')} />
      <Button label="Explore an example" secondary onPress={() => {setBalance(120000); go('today');}} />
      <Copy variant="small" muted>Cloud email sign-in will be connected in the account integration task.</Copy>
    </Card>}
    {page === 'intent' && <Card>
      <Copy variant="title">What would you like help with?</Copy>
      {choices.map(c => <Chip key={c} label={c} active={intent === c} onPress={() => setIntent(c)} />)}
      <Button label="Continue" onPress={() => go('account')} />
    </Card>}
    {page === 'account' && <Card>
      <Copy variant="title">How much is in your main account?</Copy>
      {moneyFields}<Button label="Save and continue" onPress={saveMoney} />
      <Button label="I’ll add this later" secondary onPress={() => go('income-profile')} />
    </Card>}
    {page === 'income-profile' && <Card>
      <Copy variant="title">How does your income arrive?</Copy>
      {['Regular', 'Irregular', 'Mixed', 'Not sure yet'].map(c => <Chip key={c} label={c} active={incomeType === c} onPress={() => setIncomeType(c)} />)}
      <Copy muted>You can add amounts and dates later. Expected income does not increase your balance.</Copy>
      <Button label="Open Today" onPress={() => go('today')} />
    </Card>}
    {['today', 'plan', 'assistant'].includes(page) && <View accessibilityRole="tablist" style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.sm}}>
      {tabs.map(t => <Chip key={t.page} label={t.label} active={page === t.page} onPress={() => go(t.page)} />)}
    </View>}
    {page === 'today' && <>
      <Card><Copy muted>Your money · Main account</Copy><Copy variant="money">{balance === null || scenario === 'empty' ? 'Not provided' : format(balance)}</Copy><Copy variant="small" muted>{scenario === 'stale' ? 'Example balance needs an update' : 'Manually entered · this preview session'}</Copy></Card>
      <Card soft>
        <View style={{flexDirection: 'row', alignItems: 'center', gap: space.sm}}><View style={{flex: 1}}><Copy variant="title">{balance === null || scenario === 'empty' ? 'Start with your balance' : action === 'planned' ? 'Your subscription review is planned' : action === 'completed' ? 'Your review is complete' : 'Review a recurring payment'}</Copy></View><IconButton label="Explain this recommendation" onPress={() => {setExplanation(true); go('assistant');}}><Copy>ⓘ</Copy></IconButton></View>
        <Copy muted>{balance === null || scenario === 'empty' ? 'A known balance helps us plan. You can still explore statement analysis.' : action === 'completed' ? 'You have reviewed this service. Your balance is unchanged; no service was cancelled by Vela.' : 'Check whether Example Streaming is still useful to you. No need to decide now.'}</Copy>
        <Button label={balance === null || scenario === 'empty' ? 'Add balance' : 'Open my plan'} onPress={() => go(balance === null || scenario === 'empty' ? 'balance' : 'plan')} />
      </Card>
      <Button label="Add income" onPress={() => {setIncluded(null); setReplacement(''); go('income');}} />
      <Button label="Update balance" secondary onPress={() => go('balance')} />
      <Button label="Profile & data" secondary onPress={() => go('settings')} />
    </>}
    {page === 'plan' && <>
      <Card><Copy variant="title">{action === 'none' ? 'No accepted step yet' : action === 'planned' ? 'Review Example Streaming' : 'Review completed'}</Copy><Copy muted>Example evidence: €12.99 in July, August and September. You decide whether to keep the service.</Copy>
        {action === 'none' && <Button label="Add review to my plan" onPress={() => setAction('planned')} />}
        {action === 'planned' && <><Button label="I’ve reviewed this service" onPress={() => setAction('completed')} /><Button label="Cancel review" secondary onPress={() => setAction('none')} /></>}
        <Copy variant="small" muted>This review never changes your balance or cancels a service.</Copy>
      </Card>
      <Card><Copy variant="title">Your goals</Copy><Copy muted>No goal yet. You can decide what matters after exploring your money.</Copy><Copy variant="small">Selected focus: {intent}</Copy></Card>
      <Card><Copy variant="title">Upcoming commitments</Copy><Copy muted>Not provided yet. Unknown commitments are not treated as zero.</Copy></Card>
    </>}
    {page === 'assistant' && <>
      {explanation && <Card soft><Copy variant="title">Why this step?</Copy><Copy>Reviewing a recurring payment helps you choose what to keep. Based on example-subscriptions-v1, not your bank data.</Copy><Button label="Show supporting transactions" secondary onPress={() => go('evidence')} /></Card>}
      {['Explain my next step', 'Review my spending', 'Check recurring payments', 'What if I choose a smaller step?'].map(q => <Chip key={q} label={q} onPress={() => ask(q)} />)}
      {chat.map((m, i) => <Card key={i}><Copy variant="title">{m.question}</Copy><Copy>{m.answer}</Copy></Card>)}
      <Field label="Ask about this example" value={input} onChangeText={setInput} />
      <Button label="Ask in preview" disabled={!input.trim()} onPress={() => ask(input.trim())} />
      <Button secondary label="Analyse an example statement" onPress={() => go('import')} />
    </>}
    {(page === 'income' || page === 'balance') && <Card>
      {moneyFields}
      {page === 'income' && <><Copy variant="title">Is it already in your balance?</Copy>
        <Chip label="No — add it to my balance" active={included === 'add'} onPress={() => setIncluded('add')} />
        <Chip label="Yes — record income only" active={included === 'included'} onPress={() => setIncluded('included')} />
        <Chip label="Not sure — enter current balance" active={included === 'replace'} onPress={() => setIncluded('replace')} />
        {included === 'replace' && <Field label="Current account balance (EUR)" numeric value={replacement} onChangeText={setReplacement} />}
      </>}
      <Copy muted>{page === 'balance' ? 'This replaces your known balance. The difference is not recorded as spending or income.' : 'Only the choice above determines whether your balance changes.'}</Copy>
      <Button label="Save in preview" onPress={saveMoney} />
    </Card>}
    {page === 'evidence' && <Card>
      <Copy variant="title">Evidence for this recommendation</Copy>
      <Copy muted>example-subscriptions-v1 · synthetic July–September statement · three payments</Copy>
      {['2026-07-05', '2026-08-05', '2026-09-05'].map(date => <Row key={date} label={`${date} · Example Streaming`} value="-€12.99" />)}
      <Copy>These recurring payments suggest a subscription. They do not tell us whether the service is useful to you.</Copy>
      <Copy variant="small" muted>Viewing this evidence does not import a file or change your balance.</Copy>
    </Card>}
    {page === 'import' && <Card>
      <Copy variant="title">Understand recurring spending</Copy><Copy muted>This example has three EUR transactions across July–September. Importing does not change money, goals or debt.</Copy>
      {importStage === 'choose' && <><Button label="Read synthetic statement" onPress={() => setImportStage('reading')} /><Button label="Preview an unsupported-file error" secondary onPress={() => setImportStage('error')} /></>}
      {importStage === 'reading' && <><Copy>Reading example transactions…</Copy><Button label="Reading…" loading onPress={() => {}} /></>}
      {importStage === 'error' && <><Notice>This example file could not be read. Choose a supported CSV or PDF and try again.</Notice><Button label="Try the example again" onPress={() => setImportStage('choose')} /></>}
      {(importStage === 'review' || importStage === 'saved') && <>
        {['2026-07-05', '2026-08-05', '2026-09-05'].map(date => <Row key={date} label={`${date} · Example Streaming`} value="−€12.99" />)}
        <Copy>Possible subscription · {subscription}</Copy>
        <Button secondary label="Yes, this is a subscription" onPress={() => setSubscription('confirmed')} />
        <Button secondary label="This is not a subscription" onPress={() => setSubscription('rejected')} />
        {importStage === 'review' ? <Button label="Save example analysis" onPress={() => setImportStage('saved')} /> : <Notice>Example analysis saved in this session. Your balance is unchanged.</Notice>}
      </>}
    </Card>}
    {page === 'settings' && <>
      <Card><Row label="Focus" value={intent} /><Row label="Income type" value={incomeType} /><Row label="Overview currency" value="EUR" /><Copy muted>These preview preferences disappear when the screen unmounts.</Copy></Card>
      <Button label="Statements & analysis" onPress={() => go('import')} /><Button secondary label="Reminders" onPress={() => go('reminders')} />
      <Notice>Personal export, account deletion, cloud sign-in and EUR/HUF valuation will be integrated in their own tasks.</Notice>
    </>}
    {page === 'reminders' && <Card>
      <Copy variant="title">A rhythm that suits you</Copy><Copy muted>Optional. Your device will not schedule real notifications in this preview.</Copy>
      <Chip label={reminders ? 'Reminders enabled in preview' : 'Reminders off'} active={reminders} onPress={() => {setReminders(v => !v); setReminderSaved(false);}} />
      {reminders && <>{['Daily', 'Weekly', 'Every N days'].map(f => <Chip key={f} label={f} active={frequency === f} onPress={() => {setFrequency(f); setReminderSaved(false);}} />)}
        {frequency === 'Weekly' && ['Monday', 'Wednesday', 'Friday'].map(day => <Chip key={day} label={day} active={weekday === day} onPress={() => setWeekday(day)} />)}
        {frequency === 'Every N days' && <Field label="Days between reminders" numeric value={interval} onChangeText={setInterval} />}
        <Field label="Time (24-hour HH:MM)" value={time} onChangeText={setTime} />
      </>}
      <Button label="Save preview preference" onPress={() => {
        if (reminders && (!/^([01]\d|2[0-3]):[0-5]\d$/.test(time) || (frequency === 'Every N days' && !/^[1-9]\d{0,2}$/.test(interval)))) {setError('Enter a valid time and a whole number of days.'); return;}
        setError(''); setReminderSaved(true);
      }} />
      {Boolean(error) && <Notice>{error}</Notice>}{reminderSaved && <Notice>Preference saved in this preview only. No permission requested or notification scheduled.</Notice>}
    </Card>}
    <Card><Copy variant="small" muted>Preview controls · simulate states</Copy>
      <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.sm}}>{(['ready', 'empty', 'offline', 'stale', 'conflict', 'unavailable'] as Scenario[]).map(s => <Chip key={s} label={s} active={scenario === s} onPress={() => setScenario(s)} />)}</View>
      {scenario !== 'ready' && <Notice>{scenario === 'offline' ? 'Offline example. Reading and drafts remain available; money changes are blocked.' : scenario === 'conflict' ? 'Another-device conflict example. Money changes require refreshed data.' : scenario === 'unavailable' ? 'AI unavailable example. Your data remains accessible.' : scenario === 'stale' ? 'Old balance example. Update before a money action.' : 'Missing-data example. Unknown is not zero.'}</Notice>}
    </Card>
  </Screen>;
}
