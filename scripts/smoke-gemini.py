"""Two tiny synthetic capability requests. No prompts, secrets or errors are logged."""
import asyncio
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root/'services/api'))
load_dotenv(root/'services/api/.env')
from google import genai
from google.genai import types
from vela.ai import MODELS, Quotas


async def main():
    local = root/'.local'
    local.mkdir(exist_ok=True)
    quotas = Quotas(local/'quota.db')
    results = []
    for model in MODELS:
        selected = quotas.reserve(model)
        if selected != model:
            results.append({'requested_model': model, 'status': 'quota-unavailable'})
            continue
        try:
            client = genai.Client(api_key=os.environ['GEMINI_API_KEY'], http_options=types.HttpOptions(
                timeout=12000, retry_options=types.HttpRetryOptions(attempts=1)))
            async with client.aio as ai:
                response = await asyncio.wait_for(ai.models.generate_content(model=model,
                    contents='Return exactly the JSON object {"ok":true}.',
                    config=types.GenerateContentConfig(response_mime_type='application/json', max_output_tokens=32)), timeout=15)
            if json.loads(response.text) != {'ok': True}:
                raise ValueError('Unexpected response')
            results.append({'requested_model': model, 'status': 'pass', 'returned_model': response.model_version})
        except Exception as exc:
            results.append({'requested_model': model, 'status': 'blocked-or-failed', 'error_type': type(exc).__name__})
            quotas.cooldown(model)
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'synthetic_only': True, 'results': results}
    (local/'gemini-smoke.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    if not all(r['status'] == 'pass' for r in results):
        sys.exit(1)


asyncio.run(main())
