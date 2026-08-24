# Vela Telegram Financial Assistant & Ingestion Bot

This Telegram bot integrates directly with the **Vela Financial Ingestion Pipeline** and Multi-Agent AI Advisors.

## Features
- ⚡ **Instant Expense Logging**: Send simple messages like `Кофе 4.5`, `SPAR 28.50`, or `Такси 12` in Telegram. The bot parses the amount, normalizes the merchant, categorizes the expense, and syncs it with the mobile app in real time.
- 🤖 **Chat with AI Advisors**: Ask financial questions directly in Telegram (routed to Vela Coordinator & Specialist Agents).
- 🔄 **Real-Time Synchronization**: Any logged transaction instantly reflects on the mobile dashboard.

## How to Run

```bash
cd telegram_bot
python vela_telegram_bot.py
```
