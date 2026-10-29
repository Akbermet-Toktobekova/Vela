"""Run an isolated synthetic API for a separately designed frontend. No .env loading."""
import argparse
from datetime import date, timedelta
import json
import os
from pathlib import Path
import secrets
import socket
import sys
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/api'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', action='append', default=[], help='Exact frontend origin; repeat for multiple origins.')
    parser.add_argument('--empty', action='store_true', help='Start empty to exercise onboarding.')
    args = parser.parse_args()
    # Never inherit real service/database/AI configuration or load .env.
    os.environ['APP_MODE'] = 'local'
    os.environ['ENABLE_GEMINI'] = 'false'
    from vela.main import create_app
    from vela.personal import Account
    from vela.planning import PlanningState, Goal, Bill
    import uvicorn

    base = ROOT / '.local' / 'frontend-sandboxes'
    base.mkdir(parents=True, exist_ok=True)
    folder = Path(mkdtemp(prefix='synthetic-', dir=base))
    token = secrets.token_urlsafe(32)
    origins = args.origin or ['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000']
    app = create_app(f'sqlite:///{folder / "synthetic.db"}', token, local_dir=folder, frontend_origins=origins)
    if not args.empty:
        today = date.today()
        def seed(state):
            state.personal.accounts = [Account(id='synthetic-eur', name='Synthetic account', currency='EUR', balance=100000, confirmed_on=today)]
            state.personal.planning = PlanningState(active=True, account_id='synthetic-eur', horizon=today+timedelta(days=30),
                protected=10000, bills_confirmed=True, debts_confirmed=True, goal=Goal(name='Example reserve', target=100000),
                bills=[Bill(id='synthetic-essentials', label='Example essentials', amount=80000, due=today+timedelta(days=7))])
        app.state.store.mutate('local-demo', 'synthetic-seed-0001', 0, {'kind': 'synthetic_frontend_seed'}, seed, lambda s: {'revision': s.revision})

    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        if port in (8000, 8001, 8002, 8003):
            raise RuntimeError('OS chose a protected port; rerun to select another.')
        connection = {'url': f'http://127.0.0.1:{port}', 'token': token, 'synthetic': True,
                      'origins': origins, 'database': str(folder / 'synthetic.db')}
        (folder / 'connection.json').write_text(json.dumps(connection, indent=2), encoding='utf-8')
        print(f'SYNTHETIC API {connection["url"]}', flush=True)
        print(f'Connection details (private, do not publish): {folder / "connection.json"}', flush=True)
        print('AI disabled. Ctrl+C stops only this server. Data stays in this unique synthetic folder.', flush=True)
        try:
            uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, access_log=False)).run(sockets=[sock])
        finally:
            app.state.store.engine.dispose()


if __name__ == '__main__':
    main()
