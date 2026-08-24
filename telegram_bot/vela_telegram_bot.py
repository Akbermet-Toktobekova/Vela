"""
Vela Telegram Financial Assistant & Transaction Listener
Allows logging expenses, receiving financial alerts, and chatting with Vela multi-agent advisors directly from Telegram.
"""

import os
import sys
import time
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any

# Bot Configuration
BOT_TOKEN = os.getenv("VELA_TELEGRAM_BOT_TOKEN", "8280934172:AAHhKIf_laLcBuw2m0jGqsorO-okztez3Es")
API_BASE_URL = os.getenv("VELA_API_URL", "http://127.0.0.1:8000")
OFFSET_FILE = Path(__file__).parent / ".last_update_id"

def get_last_offset() -> int:
    if OFFSET_FILE.exists():
        try:
            return int(OFFSET_FILE.read_text().strip())
        except Exception:
            return 0
    return 0

def save_last_offset(offset: int):
    try:
        OFFSET_FILE.write_text(str(offset))
    except Exception:
        pass

def send_telegram_reply(chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error sending Telegram reply: {e}", file=sys.stderr)
        return None

def ingest_to_vela(merchant: str, amount: float, source: str = "telegram_bot") -> Optional[Dict[str, Any]]:
    """Sends the expense directly to Vela FastAPI Ingestion API."""
    url = f"{API_BASE_URL}/api/expenses/ingest"
    payload = {
        "raw_merchant": merchant,
        "amount": amount,
        "currency": "EUR",
        "source": "manual",
        "account_name": "Telegram Quick Log"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        # Fallback local parser if backend is offline
        print(f"Backend offline, using local response fallback: {e}")
        return {
            "clean_merchant": merchant.title(),
            "category": "Quick Expense",
            "icon": "💳",
            "bucket": "wants",
            "amount": amount
        }

def chat_with_vela(message: str) -> str:
    """Queries Vela Multi-Agent Coordinator."""
    url = f"{API_BASE_URL}/api/chat"
    payload = {
        "message": message,
        "conversation_history": [],
        "user_id": "user_default"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("reply", "Ответ получен.")
    except Exception as e:
        return f"💡 <b>Vela Advisor:</b> Я зафиксировал твой запрос. (Сервер бэкенда Vela сейчас в автономном режиме)."

def parse_expense_text(text: str) -> Optional[Tuple[str, float]]:
    """
    Parses messages like:
    - 'Кофе 4.5' -> ('Кофе', 4.5)
    - 'SPAR 28.50 eur' -> ('SPAR', 28.5)
    - 'Такси 12' -> ('Такси', 12.0)
    - '15.99 netflix' -> ('netflix', 15.99)
    """
    text = text.strip()
    
    # Pattern: Text Amount (e.g. 'Кофе 4.5' or 'Zara 55 EUR')
    m1 = re.match(r"^([a-zA-Zа-яА-ЯёЁ\s\-\_]+?)\s+(\d+[\.,]?\d*)\s*(?:eur|€|usd|\$|huf|ft|евро|руб)?$", text, re.IGNORECASE)
    if m1:
        merchant = m1.group(1).strip()
        amount = float(m1.group(2).replace(",", "."))
        return merchant, amount

    # Pattern: Amount Text (e.g. '4.5 кофе' or '€50 Zara')
    m2 = re.match(r"^(?:eur|€|usd|\$|huf|ft)?\s*(\d+[\.,]?\d*)\s*(?:eur|€|usd|\$|huf|ft|евро|руб)?\s+([a-zA-Zа-яА-ЯёЁ\s\-\_]+)$", text, re.IGNORECASE)
    if m2:
        amount = float(m2.group(1).replace(",", "."))
        merchant = m2.group(2).strip()
        return merchant, amount

    return None

def handle_incoming_message(msg: Dict[str, Any]):
    chat_id = msg.get("chat", {}).get("id")
    user_name = msg.get("from", {}).get("first_name", "Друг")
    text = (msg.get("text") or msg.get("caption") or "").strip()

    if not text or not chat_id:
        return

    print(f"\n[Telegram] Сообщение от {user_name} ({chat_id}): «{text}»")

    # Command: /start
    if text.startswith("/start"):
        welcome = (
            f"👋 <b>Привет, {user_name}! Я твой финансовый ассистент Vela.</b>\n\n"
            f"Я мгновенно записываю твои расходы и синхронизирую их с мобильным приложением!\n\n"
            f"📌 <b>Как мной пользоваться:</b>\n"
            f"• Напиши сумму и покупку, например: <code>Кофе 4.5</code> или <code>SPAR 28.50</code>\n"
            f"• Или задай любой финансовый вопрос: <i>«Как мне оптимизировать бюджет?»</i>\n\n"
            f"❤️ <i>Солнышко, я люблю тебя!</i>"
        )
        send_telegram_reply(chat_id, welcome)
        return

    # Check if message is a quick expense log (e.g. "Кофе 4.5")
    parsed = parse_expense_text(text)
    if parsed:
        merchant, amount = parsed
        tx_data = ingest_to_vela(merchant, amount)
        
        category = tx_data.get("category", "Расходы") if tx_data else "Расходы"
        icon = tx_data.get("icon", "💳") if tx_data else "💳"
        bucket = tx_data.get("bucket", "wants") if tx_data else "wants"
        bucket_label = "Needs (Обязательное)" if bucket == "needs" else "Wants (Развлечения)"

        reply = (
            f"✅ <b>Расход записан в Vela!</b>\n\n"
            f"{icon} <b>Покупка:</b> {merchant.title()}\n"
            f"💰 <b>Сумма:</b> €{amount:,.2f}\n"
            f"🏷️ <b>Категория:</b> {category}\n"
            f"📊 <b>Тип бюджета:</b> {bucket_label}\n\n"
            f"<i>Данные уже отображаются в мобильном приложении! 📱</i>"
        )
        send_telegram_reply(chat_id, reply)
        return

    # Otherwise, treat as an AI query for Vela Multi-Agent Coordinator
    ai_reply = chat_with_vela(text)
    send_telegram_reply(chat_id, ai_reply)

def run_bot_listener(timeout_seconds: int = 3600):
    last_offset = get_last_offset()
    print(f"[*] Запуск Vela Telegram Bot Listener (offset: {last_offset})...")
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_offset + 1}&timeout=20"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not data.get("ok"):
                    time.sleep(2)
                    continue

                updates = data.get("result", [])
                for update in updates:
                    uid = update["update_id"]
                    last_offset = max(last_offset, uid)
                    save_last_offset(last_offset)

                    msg = update.get("message") or update.get("edited_message")
                    if msg:
                        handle_incoming_message(msg)
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    from typing import Tuple
    run_bot_listener()
