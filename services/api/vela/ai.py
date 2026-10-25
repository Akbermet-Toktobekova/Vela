"""Gemini access with per-model quota accounting. Financial calculations never come from a model."""
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MODELS = ("gemini-3.1-flash-lite", "gemini-3.5-flash-lite")
# Routing: chat (frequent, short) prefers 3.1; document reading (rare, long) prefers 3.5.
# Each falls back to the other model when its own budget or the provider rejects a request.
ROUTES = {"chat": MODELS[0], "document": MODELS[1], "categorize": MODELS[1]}
LIMITS = {m: {"rpm": 15, "tpm": 250_000, "rpd": 500} for m in MODELS}
APP_LIMITS = {"rpm": 12, "tpm": 225_000, "rpd": 450}
PACIFIC = ZoneInfo("America/Los_Angeles")


class AIUnavailable(Exception):
    pass


class Quotas:
    """Cross-process SQLite reservations survive restarts; requests are never refunded.

    This ledger tracks this app only. Other clients using the same Google project
    require a shared gateway. Provider 429 always overrides our local estimate.
    """
    def __init__(self, path: Path):
        self.path = path
        with self.connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS usage (model TEXT, ts REAL, day TEXT, tokens INTEGER)")
            c.execute("CREATE INDEX IF NOT EXISTS usage_window ON usage(model,ts)")
            c.execute("CREATE TABLE IF NOT EXISTS cooldown (model TEXT PRIMARY KEY, until REAL)")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def reserve(self, preferred: str, tokens: int = 2048, now: float | None = None) -> str | None:
        now = time.time() if now is None else now
        day = datetime.fromtimestamp(now, PACIFIC).date().isoformat()
        with self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            order = [preferred] + [m for m in MODELS if m != preferred]
            for model in order:
                limits = LIMITS[model]
                cool = c.execute("SELECT until FROM cooldown WHERE model=?", (model,)).fetchone()
                if cool and cool[0] > now:
                    continue
                rpm, tpm = c.execute("SELECT COUNT(*),COALESCE(SUM(tokens),0) FROM usage WHERE model=? AND ts>?", (model, now-60)).fetchone()
                rpd = c.execute("SELECT COUNT(*) FROM usage WHERE model=? AND day=?", (model, day)).fetchone()[0]
                # Leave headroom: use at most 12 RPM, 225K TPM and 450 RPD in the application.
                if rpm >= min(APP_LIMITS["rpm"], limits["rpm"]) or tpm + tokens > APP_LIMITS["tpm"] or rpd >= min(APP_LIMITS["rpd"], limits["rpd"]):
                    continue
                c.execute("INSERT INTO usage VALUES(?,?,?,?)", (model, now, day, tokens))
                return model
        return None

    def cooldown(self, model: str, seconds: int = 60):
        with self.connect() as c:
            c.execute("INSERT OR REPLACE INTO cooldown VALUES(?,?)", (model, time.time()+seconds))

    def usage(self, now: float | None = None) -> list[dict]:
        now = time.time() if now is None else now
        day = datetime.fromtimestamp(now, PACIFIC).date().isoformat()
        out = []
        with self.connect() as c:
            for model in MODELS:
                rpm, tpm = c.execute("SELECT COUNT(*),COALESCE(SUM(tokens),0) FROM usage WHERE model=? AND ts>?", (model, now-60)).fetchone()
                rpd = c.execute("SELECT COUNT(*) FROM usage WHERE model=? AND day=?", (model, day)).fetchone()[0]
                cool = c.execute("SELECT until FROM cooldown WHERE model=?", (model,)).fetchone()
                out.append({"model": model, "requests_today": rpd, "daily_limit": APP_LIMITS["rpd"],
                            "requests_last_minute": rpm, "tokens_last_minute": tpm,
                            "cooling_down": bool(cool and cool[0] > now)})
        return out


def enabled() -> bool:
    return os.getenv("ENABLE_GEMINI") == "true" and bool(os.getenv("GEMINI_API_KEY"))


def estimate_tokens(*parts) -> int:
    return sum(len(p) if isinstance(p, (bytes, bytearray)) else len(str(p)) for p in parts) // 3 + 256


async def generate(quotas: Quotas, route: str, contents, config: dict, tokens: int, timeout_ms: int = 30_000):
    """Runs one generate_content call, trying the preferred model then the other one.

    Returns (response, model). Provider errors are never logged: they can echo request content.
    """
    if not enabled():
        raise AIUnavailable("The AI service is turned off. Set ENABLE_GEMINI=true and GEMINI_API_KEY in services/api/.env.")
    from google import genai
    from google.genai import types
    preferred = ROUTES[route]
    tried: set[str] = set()
    last_error = "busy"
    for _ in range(len(MODELS)):
        model = quotas.reserve(preferred, tokens=min(tokens, APP_LIMITS["tpm"]))
        if model is None or model in tried:
            break
        tried.add(model)
        try:
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                                  http_options=types.HttpOptions(timeout=max(timeout_ms, 10_000),
                                                                 retry_options=types.HttpRetryOptions(attempts=1)))
            async with client.aio as ai:
                response = await ai.models.generate_content(model=model, contents=contents,
                                                            config=types.GenerateContentConfig(**config))
            if not response.text:
                raise ValueError("empty response")
            return response, model
        except Exception as exc:  # noqa: BLE001 - provider errors are mapped, not logged
            code = getattr(exc, "code", None)
            last_error = "rate-limited" if code == 429 else "failed"
            quotas.cooldown(model, 60 if code == 429 else 20)
    raise AIUnavailable("The AI service is busy or unreachable right now. Try again in a minute."
                        if last_error != "failed" else "The AI service could not complete this request. Try again.")


def money(amount: int) -> str:
    sign = "−" if amount < 0 else ""
    euros, cents = divmod(abs(amount), 100)
    return f"{sign}€{euros:,}.{cents:02d}"


def parse_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("\n")+1:] if "\n" in text else text
    return json.loads(text)
