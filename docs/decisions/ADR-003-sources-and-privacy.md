# ADR-003 — Sources, imports, and future open banking

`TransactionSource.fetch(user_id, since)` abstracts synthetic, CSV, and replay inputs. Agents receive normalized transaction records only. Synthetic data is checked into the repository; imported content is stored only in the ignored local SQLite file. Source CSV uploads are processed in memory and not written to disk.

CSV detection supports UTF-8 BOM or Windows-1250, comma/semicolon/tab/pipe delimiters, decimal comma/point, spaces in amounts, signed amounts or debit/credit columns, and a manual mapping. Ambiguous numeric dates default to day-first, disclosed in the result; `date_format` overrides it. Every rejected row has its input line and an error. Identical uploaded file bytes plus line number identify imported transactions; re-import is idempotent. Different exports of the same transactions may duplicate records, which remains a limitation.

Imports provide historical analysis and never infer the current account balance or trigger simulated transfers. Update the explicit cash balance after reviewing a statement. Replay uses chronological synthetic events; scheduled rules run after known same-day outflows and at most once per rule/date. A synthetic outflow exceeding cash is flagged as declined rather than silently creating an unsupported negative balance.

Future `OpenBankingSource` is deliberately not implemented. A future read-only PSD2 aggregator adapter would need consent, regional/provider coverage, token lifecycle, account/currency mapping, duplicate reconciliation, data retention, and security review. It would normalize records into the same interface and must not expose payment initiation capabilities. No compliance certification is asserted.

The fake provider runs locally. Anthropic is optional and requires explicit environment configuration. With it enabled, chat text and relevant structured facts leave the device. Cache entries are local, ignored, and cleared by delete-data. In this unencrypted prototype, deletion removes application records, not forensic remnants or backups. No authentication: bind to loopback, and do not expose the server publicly.
