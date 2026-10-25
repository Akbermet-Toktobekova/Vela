"""Create local demo credentials without printing or embedding them in the mobile bundle."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
env = root / 'services/api/.env'
if not env.exists():
    env.write_text('APP_MODE=demo\nDEMO_API_TOKEN=' + secrets.token_urlsafe(32) + '\nGEMINI_API_KEY=\nENABLE_GEMINI=false\n', encoding='utf-8')
    print('Created services/api/.env. Enter its DEMO_API_TOKEN on the device connection screen.')
else:
    print('Existing services/api/.env preserved.')
