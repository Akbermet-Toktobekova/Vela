import React, { useState } from 'react';
import { View } from 'react-native';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Chip, Copy, Field, Notice, Row, Screen } from '../components/ui';
import { StateGate } from '../components/StateGate';
import { useCommand } from '../lib/state';
import {
  aprBps,
  cents,
  Debt,
  DebtSimulationView,
  DebtsView,
  FinancialState,
  formatApr,
  money,
  request,
  StrategyResult,
} from '../lib/api';
import { space, usePalette } from '../theme';

function formatMonths(months: number | null): string {
  if (months === null) return '—';
  if (months === 0) return '0 mo';
  const yrs = Math.floor(months / 12);
  const rem = months % 12;
  if (yrs === 0) return `${months} mo`;
  return rem === 0 ? `${months} mo (${yrs}y)` : `${months} mo (${yrs}y ${rem}m)`;
}

function StrategySection({title, subtitle, result, showSavings = false}: {
  title: string;
  subtitle: string;
  result: StrategyResult;
  showSavings?: boolean;
}) {
  const p = usePalette();
  return (
    <View style={{paddingVertical: space.xs, borderBottomWidth: 0.5, borderColor: p.border, gap: 2}}>
      <Copy variant="title">{title}</Copy>
      <Copy variant="small" muted>{subtitle}</Copy>
      {result.status === 'needs_input' ? (
        <Notice>Add known interest rates and minimum payments to calculate payoff time and interest.</Notice>
      ) : result.status === 'non_amortizing' ? (
        <Notice>Minimum payment does not cover monthly interest. Increase monthly payment to amortize.</Notice>
      ) : (
        <>
          <Row label="Payoff horizon" value={formatMonths(result.months)} />
          <Row label="Total interest" value={result.total_interest_cents !== null ? money(result.total_interest_cents) : '—'} />
          <Row label="Total paid" value={result.total_paid_cents !== null ? money(result.total_paid_cents) : '—'} />
          {showSavings && result.interest_saved_vs_baseline_cents !== null && result.months_saved_vs_baseline !== null && (
            <Row
              label="Saved vs minimums only"
              value={`${money(result.interest_saved_vs_baseline_cents)} · ${result.months_saved_vs_baseline} mo faster`}
              bold
            />
          )}
        </>
      )}
    </View>
  );
}

function DebtsContent({state}: {state: FinancialState}) {
  const p = usePalette();
  const cache = useQueryClient();
  const command = useCommand();

  const [showAdd, setShowAdd] = useState(false);
  const [label, setLabel] = useState('');
  const [balanceText, setBalanceText] = useState('');
  const [aprText, setAprText] = useState('18');
  const [minPayText, setMinPayText] = useState('');
  const [dueDayText, setDueDayText] = useState('15');
  const [kind, setKind] = useState<Debt['kind']>('credit_card');
  const [termsKnown, setTermsKnown] = useState(true);
  const [formError, setFormError] = useState('');

  const [oneOffText, setOneOffText] = useState('100');
  const [recurringText, setRecurringText] = useState('0');
  const [simError, setSimError] = useState('');

  const debtsQuery = useQuery({
    queryKey: ['debts', state.revision],
    queryFn: () => request<DebtsView>('/v1/debts'),
  });

  const simulateMutation = useMutation({
    mutationFn: (payload: {one_off_extra_cents: number; recurring_extra_cents: number}) =>
      request<DebtSimulationView>('/v1/debts/simulate', 'POST', payload),
  });

  const debts = debtsQuery.data?.debts ?? state.debts ?? [];
  const totalBalance = debts.reduce((acc, d) => acc + d.balance_cents, 0);
  const totalMinPayment = debts.reduce((acc, d) => acc + d.min_payment_cents, 0);

  const activeSim =
    simulateMutation.data?.revision === state.revision
      ? simulateMutation.data
      : debtsQuery.data?.comparison;

  function submitAddDebt() {
    try {
      if (!label.trim()) throw new Error('Enter a debt name (e.g. Visa Card, Auto Loan).');
      const balance_cents = cents(balanceText);
      if (balance_cents <= 0) throw new Error('Enter a balance above zero.');
      const apr_bps = termsKnown ? aprBps(aprText) : 0;
      const min_payment_cents = termsKnown ? cents(minPayText) : 0;
      if (termsKnown && min_payment_cents <= 0) throw new Error('Enter a minimum monthly payment above zero.');
      const due_day = Number(dueDayText.trim());
      if (!Number.isInteger(due_day) || due_day < 1 || due_day > 31) {
        throw new Error('Enter a due day of the month between 1 and 31.');
      }
      const debt: Debt = {
        id: `debt-${Date.now()}`,
        label: label.trim(),
        balance_cents,
        apr_bps,
        min_payment_cents,
        due_day,
        kind,
        terms_known: termsKnown,
      };
      setFormError('');
      command.mutate(
        {path: '/v1/debts', body: {revision: state.revision, debt}},
        {
          onSuccess: () => {
            setLabel('');
            setBalanceText('');
            setMinPayText('');
            setShowAdd(false);
            simulateMutation.reset();
            cache.invalidateQueries({queryKey: ['debts']});
          },
        },
      );
    } catch (e) {
      setFormError(e instanceof Error ? e.message : 'Check debt fields.');
    }
  }

  function removeDebt(debtId: string) {
    command.mutate(
      {path: `/v1/debts/${debtId}`, method: 'DELETE', body: {revision: state.revision}},
      {
        onSuccess: () => {
          simulateMutation.reset();
          cache.invalidateQueries({queryKey: ['debts']});
        },
      },
    );
  }

  function runPreview(presetOneOffCents?: number) {
    try {
      setSimError('');
      const one_off_extra_cents =
        presetOneOffCents !== undefined ? presetOneOffCents : oneOffText.trim() ? cents(oneOffText) : 0;
      const recurring_extra_cents = recurringText.trim() ? cents(recurringText) : 0;
      if (presetOneOffCents !== undefined) {
        setOneOffText(String(presetOneOffCents / 100));
      }
      simulateMutation.mutate({one_off_extra_cents, recurring_extra_cents});
    } catch (e) {
      setSimError(e instanceof Error ? e.message : 'Enter valid EUR amounts for preview.');
    }
  }

  const oneOffPresets = Array.from(
    new Set([2500, 5000, 10000, Math.min(25000, totalBalance)].filter(v => v > 0 && v <= Math.max(2500, totalBalance))),
  ).slice(0, 4);

  return (
    <>
      <Card>
        <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
          <Copy variant="title">Your debts ({debts.length})</Copy>
          <Button label={showAdd ? 'Close' : '+ Add debt'} small secondary onPress={() => setShowAdd(!showAdd)} />
        </View>

        {debts.length > 0 && (
          <>
            <Row label="Total debt balance" value={money(totalBalance)} bold />
            <Row label="Total monthly minimums" value={money(totalMinPayment)} />
          </>
        )}

        {showAdd && (
          <View style={{gap: space.sm, paddingVertical: space.xs}}>
            <Field label="Debt name" placeholder="e.g. Credit Card, Student Loan" value={label} onChangeText={setLabel} />
            <View style={{flexDirection: 'row', gap: space.sm}}>
              <View style={{flex: 1}}>
                <Field label="Balance (EUR)" numeric placeholder="1000" value={balanceText} onChangeText={setBalanceText} />
              </View>
              <View style={{flex: 1}}>
                <Field label="Due day (1–31)" numeric placeholder="15" value={dueDayText} onChangeText={setDueDayText} />
              </View>
            </View>

            <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
              {(['credit_card', 'personal_loan', 'overdraft', 'other'] as const).map(k => (
                <Chip key={k} label={k.replace('_', ' ')} active={kind === k} onPress={() => setKind(k)} />
              ))}
            </View>

            <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
              <Chip label="Terms known" active={termsKnown} onPress={() => setTermsKnown(true)} />
              <Chip label="APR / minimum unknown" active={!termsKnown} onPress={() => setTermsKnown(false)} />
            </View>

            {termsKnown && (
              <View style={{flexDirection: 'row', gap: space.sm}}>
                <View style={{flex: 1}}>
                  <Field label="APR (%)" numeric placeholder="18.0" value={aprText} onChangeText={setAprText} />
                </View>
                <View style={{flex: 1}}>
                  <Field label="Min payment (EUR)" numeric placeholder="50" value={minPayText} onChangeText={setMinPayText} />
                </View>
              </View>
            )}

            <Button label="Save debt" small disabled={command.isPending} onPress={submitAddDebt} />
          </View>
        )}

        {(formError || command.error) && <Notice>{formError || command.error?.message}</Notice>}

        {debts.length === 0 && (
          <Copy variant="small" muted>
            No debts recorded. Add a credit card, loan, or overdraft to compare Avalanche vs Snowball payoff and preview extra payments.
          </Copy>
        )}

        {debts.map(d => (
          <View key={d.id} style={{paddingVertical: space.xs, borderBottomWidth: 0.5, borderColor: p.border, gap: 4}}>
            <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
              <Copy>
                {d.label} ·{' '}
                <Copy variant="small" muted>
                  {d.terms_known
                    ? `${formatApr(d.apr_bps)} APR · min ${money(d.min_payment_cents)}/mo · day ${d.due_day}`
                    : `terms unknown · day ${d.due_day}`}
                </Copy>
              </Copy>
              <Copy variant="title">{money(d.balance_cents)}</Copy>
            </View>
            <View style={{flexDirection: 'row', gap: space.xs}}>
              <Button label="Remove" small secondary disabled={command.isPending} onPress={() => removeDebt(d.id)} />
            </View>
          </View>
        ))}
      </Card>

      {debts.length > 0 && activeSim && (
        <>
          <Card soft>
            <Copy variant="title">Avalanche vs Snowball comparison</Copy>
            <Copy variant="small" muted>
              Deterministic monthly calculation ({activeSim.rounding_rule}). Freed minimum payments roll into the next priority debt.
            </Copy>

            <StrategySection
              title="Avalanche (highest APR first)"
              subtitle="Minimizes total interest cost by targeting highest-rate debt first."
              result={activeSim.avalanche}
              showSavings
            />

            <StrategySection
              title="Snowball (smallest balance first)"
              subtitle="Clears individual balances sooner by targeting smallest debt first."
              result={activeSim.snowball}
              showSavings
            />

            <StrategySection
              title="Minimum payments only (baseline)"
              subtitle="Each debt paid independently at its minimum required amount."
              result={activeSim.baseline}
            />
          </Card>

          <Card>
            <Copy variant="title">Preview extra payment (read-only)</Copy>
            <Copy variant="small" muted>
              Simulate a one-off or recurring extra payment without changing your saved plan or account balances.
            </Copy>

            {oneOffPresets.length > 0 && (
              <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: space.xs}}>
                {oneOffPresets.map(v => (
                  <Chip
                    key={v}
                    label={`+${money(v)} one-off`}
                    active={oneOffText === String(v / 100)}
                    onPress={() => runPreview(v)}
                  />
                ))}
              </View>
            )}

            <View style={{flexDirection: 'row', gap: space.sm}}>
              <View style={{flex: 1}}>
                <Field
                  label="One-off extra (EUR)"
                  numeric
                  placeholder="100"
                  value={oneOffText}
                  onChangeText={v => {
                    setOneOffText(v);
                    simulateMutation.reset();
                  }}
                />
              </View>
              <View style={{flex: 1}}>
                <Field
                  label="Monthly extra (EUR)"
                  numeric
                  placeholder="0"
                  value={recurringText}
                  onChangeText={v => {
                    setRecurringText(v);
                    simulateMutation.reset();
                  }}
                />
              </View>
            </View>

            <Button
              label="Preview impact"
              secondary
              disabled={simulateMutation.isPending}
              onPress={() => runPreview()}
            />

            {(simError || simulateMutation.error) && (
              <Notice>{simError || simulateMutation.error?.message}</Notice>
            )}

            {activeSim.one_off_preview && (
              <View style={{gap: 2, paddingTop: space.xs}}>
                <Row
                  label="One-off extra applied"
                  value={
                    activeSim.one_off_preview.applied_extra_cents < activeSim.one_off_preview.requested_extra_cents
                      ? `${money(activeSim.one_off_preview.applied_extra_cents)} (capped at balance)`
                      : money(activeSim.one_off_preview.applied_extra_cents)
                  }
                />
                {activeSim.one_off_preview.status === 'paid' ? (
                  <>
                    <Row label="New payoff horizon" value={formatMonths(activeSim.one_off_preview.months)} />
                    <Row
                      label="New total interest"
                      value={
                        activeSim.one_off_preview.total_interest_cents !== null
                          ? money(activeSim.one_off_preview.total_interest_cents)
                          : '—'
                      }
                    />
                    {activeSim.one_off_preview.interest_saved_cents !== null &&
                      activeSim.one_off_preview.months_saved !== null && (
                        <Row
                          label="Interest & time saved"
                          value={`${money(activeSim.one_off_preview.interest_saved_cents)} · ${activeSim.one_off_preview.months_saved} mo faster`}
                          bold
                        />
                      )}
                  </>
                ) : (
                  <Notice>
                    {activeSim.one_off_preview.status === 'needs_input'
                      ? 'Confirm all debt terms to preview payoff savings.'
                      : 'Remaining payments still do not cover monthly interest.'}
                  </Notice>
                )}
              </View>
            )}
          </Card>
        </>
      )}
    </>
  );
}

export default function DebtsScreen() {
  return (
    <Screen title="Debts & payoff" eyebrow="Vela">
      <StateGate allowEmpty>{state => <DebtsContent state={state} />}</StateGate>
    </Screen>
  );
}
