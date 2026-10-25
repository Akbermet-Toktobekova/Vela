import os
from pathlib import Path
import sys
from dotenv import load_dotenv
import uvicorn

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'services/api'))
load_dotenv(root / 'services/api/.env')
# Bind to 0.0.0.0 by default so both local simulators and LAN physical devices (via QR code) can connect.
uvicorn.run('vela.main:create_app', factory=True, host=os.getenv('API_HOST', '0.0.0.0'), port=int(os.getenv('API_PORT', '8000')), access_log=False)
