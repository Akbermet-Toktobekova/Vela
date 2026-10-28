import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

function readUriAsBase64(uri: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.onload = () => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const res = typeof reader.result === 'string' ? reader.result : '';
        const comma = res.indexOf(',');
        resolve(comma >= 0 ? res.slice(comma + 1) : res);
      };
      reader.onerror = () => reject(new Error('Could not read selected file.'));
      reader.readAsDataURL(xhr.response as Blob);
    };
    xhr.onerror = () => reject(new Error('Could not open selected file.'));
    xhr.responseType = 'blob';
    xhr.open('GET', uri, true);
    xhr.send(null);
  });
}

export interface Obligation { id: string; label: string; amount: number; due: string; kind: 'rent' | 'living' | 'debt' | 'other' }
export interface Debt {
  id: string; label: string; balance_cents: number; apr_bps: number;
  min_payment_cents: number; due_day: number;
  kind: 'credit_card' | 'personal_loan' | 'overdraft' | 'other';
  terms_known: boolean;
}
export type AmortizationStatus = 'paid' | 'non_amortizing' | 'needs_input' | 'unsupported';
export interface DebtPayoffSummary {
  debt_id: string; label: string; status: AmortizationStatus;
  months: number | null; total_interest_cents: number | null;
  total_paid_cents: number | null; principal_paid_cents: number | null;
}
export interface StrategyResult {
  strategy: 'minimum_only' | 'avalanche' | 'snowball';
  status: AmortizationStatus;
  months: number | null; total_interest_cents: number | null; total_paid_cents: number | null;
  interest_saved_vs_baseline_cents: number | null; months_saved_vs_baseline: number | null;
  debts: DebtPayoffSummary[];
}
export interface OneOffExtraPreview {
  requested_extra_cents: number; applied_extra_cents: number; target_debt_id: string | null;
  status: AmortizationStatus; months: number | null; total_interest_cents: number | null;
  total_paid_cents: number | null; interest_saved_cents: number | null; months_saved: number | null;
}
export interface DebtSimulationView {
  revision: number; status: AmortizationStatus; rounding_rule: string;
  recurring_extra_cents: number; one_off_extra_cents: number;
  baseline: StrategyResult; avalanche: StrategyResult; snowball: StrategyResult;
  one_off_preview: OneOffExtraPreview | null;
}
export interface DebtsView { revision: number; debts: Debt[]; comparison: DebtSimulationView }
export interface Snapshot {
  nickname: string; currency: 'EUR'; as_of: string; horizon: string; cash: number; saved: number;
  protected: number; goal_target: number; goal_name: string; obligations: Obligation[];
  obligations_complete: boolean; debt_known: boolean; provenance: 'synthetic' | 'manual' | 'import';
}
export interface Action { id: string; amount: number; status: 'planned' | 'completed' | 'cancelled'; created_on: string; completed_on?: string | null; can_complete: boolean }
export interface Transaction { id: string; date: string; description: string; amount: number; category: string; source: string }
export interface Summary {
  transaction_count: number; period_start: string | null; period_end: string | null;
  income: number; spending: number; top_categories: {category: string; amount: number}[];
}
export interface Breakdown { cash: number; saved: number; protected: number; bills: number; planned: number }
export interface Recommendation {
  kind: 'save' | 'clarify' | 'shortfall' | 'maintain' | 'goal_reached';
  amount: number; message: string; policy?: string | null;
  clarify_field?: 'debt_known' | 'obligations_complete' | 'refresh' | null;
}
export interface FinancialState {
  revision: number; snapshot: Snapshot | null; available: number; breakdown: Breakdown;
  actions: Action[]; debts: Debt[]; recommendation: Recommendation; summary: Summary;
  history: {event: string; revision: number}[]; mode: 'local';
}
export interface Preview { revision: number; amount: number; eligible: boolean; remaining: number; goal_after: number }
export interface Recurring { id: string; label: string; amount: number; next_due: string; occurrences: number; kind: Obligation['kind'] }
export interface ImportPreview {
  id: string; filename: string; file_type: 'csv' | 'xlsx' | 'pdf' | 'image'; parser: 'local' | 'gemini';
  model: string | null; currency: string; period_start: string | null; period_end: string | null;
  opening_balance: number | null; closing_balance: number | null; income: number; spending: number;
  transactions: Transaction[]; recurring: Recurring[]; warnings: string[];
}
export interface ChatMessage { role: 'user' | 'assistant'; content: string }
export interface ChatReply { reply: string; source: 'gemini' | 'local'; model: string | null; revision: number }
export interface AIStatus {
  enabled: boolean; routes: Record<string, string>;
  models: {model: string; requests_today: number; daily_limit: number; requests_last_minute: number; tokens_last_minute: number; cooling_down: boolean}[];
}
export interface LessonQuizView {
  question: string; options: string[]; correct_index: number; explanation: string;
}
export interface LessonSummaryView {
  id: string; title: string; summary: string; related_actions: string[];
  reviewed: boolean; completed: boolean; selected_index: number | null;
  correct: boolean | null; completed_on: string | null; recommended_for_current_step: boolean;
}
export interface LessonDetailView extends LessonSummaryView {
  body_markdown: string; paragraphs: string[]; quiz: LessonQuizView;
}
export interface LessonsListView {
  revision: number; active_action_id: string; active_recommendation_kind: string;
  active_recommendation_message: string; recommended_lesson: LessonSummaryView | null;
  recommended_lessons: LessonSummaryView[]; completed_count: number; total_count: number;
  lessons: LessonSummaryView[];
}
export interface LessonProgressCommand {
  revision?: number | null; selected_index?: number | null; completed?: boolean;
}
export interface Connection { url: string; token: string }
let connection: Connection | null = null;
const storageKey = 'vela-demo-connection';

export async function restoreConnection(): Promise<boolean> {
  if (Platform.OS === 'web') return false;
  const saved = await SecureStore.getItemAsync(storageKey);
  if (saved) { connection = JSON.parse(saved) as Connection; return true; }
  return false;
}
export async function connect(value: Connection) {
  const url = new URL(value.url);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) throw new Error('Enter an HTTP or HTTPS API address.');
  const previous = connection;
  connection = { url: value.url.replace(/\/$/, ''), token: value.token.trim() };
  try {
    await request<FinancialState>('/v1/state');
    if (Platform.OS !== 'web') await SecureStore.setItemAsync(storageKey, JSON.stringify(connection));
  } catch (error) { connection = previous; throw error; }
}
export async function disconnect() {
  connection = null;
  if (Platform.OS !== 'web') await SecureStore.deleteItemAsync(storageKey);
}
export function apiErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail !== 'string' || /validation error|input_value=|Traceback|errors\.pydantic\.dev/i.test(detail)) return fallback;
  return detail;
}
export async function request<T>(path: string, method = 'GET', body?: unknown, key?: string, timeoutMs = 45000): Promise<T> {
  if (!connection) throw new Error('Connect to your local API first.');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${connection.url}${path}`, {
      method, signal: controller.signal,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${connection.token}`, ...(key ? {'Idempotency-Key': key} : {}) },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(apiErrorMessage(result.detail, 'Please check the amounts and dates you entered.'));
    return result as T;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw new Error('The request timed out. Try again.');
    throw error;
  } finally { clearTimeout(timeout); }
}
export async function uploadStatement(asset: {uri: string; name: string; mimeType?: string; file?: File; base64?: string}): Promise<ImportPreview> {
  if (!connection) throw new Error('Connect to your local API first.');
  if (Platform.OS !== 'web') {
    const base64 = asset.base64 || await readUriAsBase64(asset.uri);
    return request<ImportPreview>('/v1/imports/base64', 'POST', {
      filename: asset.name || 'statement',
      content_type: asset.mimeType || 'application/octet-stream',
      data_base64: base64,
    }, undefined, 140000);
  }
  const form = new FormData();
  if (asset.file) {
    form.append('file', asset.file, asset.name);
  } else {
    form.append('file', { uri: asset.uri, name: asset.name, type: asset.mimeType || 'application/octet-stream' } as unknown as Blob);
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 140000);
  try {
    const response = await fetch(`${connection.url}/v1/imports`, {
      method: 'POST', signal: controller.signal,
      headers: { Authorization: `Bearer ${connection.token}` },
      body: form,
    });
    const result = await response.json();
    if (!response.ok) throw new Error(apiErrorMessage(result.detail, 'Could not read that file.'));
    return result as ImportPreview;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw new Error('Reading the file took too long. Try a smaller file or CSV export.');
    throw error;
  } finally { clearTimeout(timeout); }
}
export const money = (cents: number) => new Intl.NumberFormat(undefined, {style: 'currency', currency: 'EUR'}).format(cents / 100);
export function cents(text: string): number {
  if (!/^\d{1,8}([.,]\d{1,2})?$/.test(text.trim())) throw new Error('Enter an amount with up to two decimal places.');
  const [whole, fractional = ''] = text.trim().replace(',', '.').split('.');
  const value = Number(whole) * 100 + Number(fractional.padEnd(2, '0'));
  if (value > 1000000000) throw new Error('This amount is above the supported limit.');
  return value;
}
export function aprBps(text: string): number {
  if (!/^\d{1,3}([.,]\d{1,2})?$/.test(text.trim())) throw new Error('Enter an APR percentage (e.g. 12.5 or 0).');
  const [whole, fractional = ''] = text.trim().replace(',', '.').split('.');
  const value = Number(whole) * 100 + Number(fractional.padEnd(2, '0'));
  if (value > 100000) throw new Error('APR cannot exceed 1000%.');
  return value;
}
export const formatApr = (bps: number) => `${(bps / 100).toFixed(bps % 100 === 0 ? 0 : 2)}%`;
export function localDate(offsetDays = 0) {
  const d = new Date();
  if (offsetDays) d.setDate(d.getDate() + offsetDays);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
