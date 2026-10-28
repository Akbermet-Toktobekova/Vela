"""Run the existing local API and Expo together; no installs, resets or embedded tokens."""
from __future__ import annotations

import argparse
import ipaddress
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "apps/mobile"
LOCAL = ROOT / ".local"
HTTP = build_opener(ProxyHandler({}))


def available_port(port: int) -> None:
    with socket.socket() as sock:
        if os.name == "nt":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            sock.bind(("0.0.0.0", port))
        except OSError as exc:
            raise RuntimeError(
                f"Port {port} is busy. Stop the previous Vela/Expo session first. "
                "This launcher will not stop another application's process."
            ) from exc
    if socket.has_ipv6:
        with socket.socket(socket.AF_INET6) as sock:
            try:
                sock.bind(("::1", port))
            except OSError as exc:
                # An unavailable IPv6 loopback is fine, an occupied one is not.
                import errno
                if exc.errno in (errno.EADDRINUSE, errno.EACCES) or getattr(exc, "winerror", None) in (10048, 10013):
                    raise RuntimeError(f"IPv6 port {port} is busy. Stop the previous session first.") from exc


def lan_address() -> str:
    # UDP connect selects a route without transmitting application data.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 9))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def fetch(url: str, token: str | None = None) -> bytes:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with HTTP.open(Request(url, headers=headers), timeout=2) as response:
        return response.read()


def wait_ready(process: subprocess.Popen, url: str, timeout: float,
               token: str | None = None, expected: bytes | None = None,
               companion: subprocess.Popen | None = None) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None or (companion and companion.poll() is not None):
            raise RuntimeError("A service exited before startup completed. See .local/dev-*.log.")
        try:
            body = fetch(url, token)
            if expected is None or expected in body:
                return
        except (OSError, URLError):
            pass
        time.sleep(0.3)
    raise RuntimeError(f"Startup timed out: {url}. See .local/dev-*.log.")


def stop(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    if os.name == "nt":
        # Kill only the process tree created by this invocation, never by image name.
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        import signal
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web", action="store_true", help="Open Expo web at localhost:8081")
    parser.add_argument("--dev-client", action="store_true", help="Use an installed development build instead of Expo Go")
    parser.add_argument("--lan-ip", help="Wi-Fi IPv4 address when automatic selection chooses a VPN/other adapter")
    parser.add_argument("--ai", action="store_true", help="Allow configured Gemini calls (may consume provider quota)")
    parser.add_argument("--check", action="store_true", help="Check dependencies and ports without starting services")
    parser.add_argument("--smoke", action="store_true", help="Start both services, verify readiness, then stop both")
    args = parser.parse_args()
    if args.web and args.dev_client:
        parser.error("--dev-client is for native devices, not --web")
    if args.lan_ip:
        try:
            ipaddress.IPv4Address(args.lan_ip)
        except ValueError:
            parser.error("--lan-ip must be an IPv4 address")

    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js was not found on PATH.")
    expo_cli = MOBILE / "node_modules/expo/bin/cli"
    if not expo_cli.is_file():
        raise RuntimeError("Mobile dependencies are missing. Run npm ci in apps/mobile, then retry.")
    result = subprocess.run(
        [sys.executable, "-c", "import dotenv, uvicorn; import vela.main"],
        cwd=ROOT / "services/api", capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(
            f"Backend dependencies are missing for {sys.executable}. "
            "Install services/api/requirements-dev.txt in your project Python environment."
        )
    available_port(8000)
    available_port(8081)
    if args.check:
        print("PASS: Python/backend imports, Node, installed Expo CLI, ports 8000/8081.")
        return 0

    subprocess.run([sys.executable, str(ROOT / "scripts/setup-local.py")], check=True)
    from dotenv import dotenv_values
    env = {**{k: v for k, v in dotenv_values(ROOT / "services/api/.env").items()
              if v is not None}, **os.environ}
    token = env.get("DEMO_API_TOKEN", "")
    if len(token) < 24 or token == "replace-with-a-random-local-token":
        raise RuntimeError("Set a random DEMO_API_TOKEN (24+ characters) in services/api/.env; existing settings were preserved.")
    if env.get("APP_MODE", "demo") not in ("demo", "local"):
        raise RuntimeError("This launcher supports only APP_MODE=demo or local.")
    if args.ai and not env.get("GEMINI_API_KEY"):
        raise RuntimeError("--ai requires GEMINI_API_KEY in the local environment.")
    env.update(API_HOST="127.0.0.1" if args.web or args.smoke else "0.0.0.0",
               API_PORT="8000", ENABLE_GEMINI="true" if args.ai else "false",
               PYTHONUNBUFFERED="1")
    ip = args.lan_ip or lan_address()
    api_url = "http://127.0.0.1:8000" if args.web or args.smoke else f"http://{ip}:8000"
    LOCAL.mkdir(exist_ok=True)
    connection_file = LOCAL / "dev-connection.txt"
    connection_file.write_text(
        f"API address: {api_url}\nAccess token: {token}\n\n"
        "Local testing credentials. Do not share or commit this file.\n", encoding="utf-8")
    print(f"API address: {api_url}\nConnection values: {connection_file}", flush=True)
    print("AI: " + ("configured Gemini enabled" if args.ai else "local fallback (no Gemini calls)"), flush=True)
    print("API logs: .local/dev-api.log\nCtrl+C stops BOTH services. Saved data remains.", flush=True)

    # Pass only the ordinary parent environment to Expo, never the backend .env.
    expo_env = dict(os.environ)
    expo_env.update(EXPO_NO_TELEMETRY="1")
    if args.smoke:
        expo_env["CI"] = "1"
    if args.lan_ip and not (args.web or args.smoke):
        expo_env["REACT_NATIVE_PACKAGER_HOSTNAME"] = ip
    expo_args = [node, str(expo_cli), "start", "--port", "8081",
                 "--localhost" if args.web or args.smoke else "--lan",
                 "--dev-client" if args.dev_client else "--go"]
    if args.web and not args.smoke:
        expo_args.append("--web")
    child_options = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
                     if os.name == "nt" else {"start_new_session": True})
    api = expo = None
    with (LOCAL / "dev-api.log").open("w", encoding="utf-8") as api_log, \
            (LOCAL / "dev-expo.log").open("w", encoding="utf-8") as expo_log:
        try:
            api = subprocess.Popen([sys.executable, str(ROOT / "scripts/run-api.py")],
                                   cwd=ROOT, env=env, stdout=api_log,
                                   stderr=subprocess.STDOUT, **child_options)
            wait_ready(api, "http://127.0.0.1:8000/v1/state", 30, token)
            print("Backend ready (authenticated state request passed). Starting Expo...", flush=True)
            expo = subprocess.Popen(expo_args, cwd=MOBILE, env=expo_env,
                                    stdout=expo_log if args.smoke else None,
                                    stderr=subprocess.STDOUT if args.smoke else None,
                                    **child_options)
            wait_ready(expo, "http://localhost:8081/status", 90,
                       expected=b"packager-status:running", companion=api)
            print("READY: API + Expo. " + ("Open http://localhost:8081" if args.web else
                  "Scan the Expo QR code, then enter values from .local/dev-connection.txt."), flush=True)
            if args.smoke:
                print("PASS: authenticated API and Expo /status. Stopping smoke session.", flush=True)
                return 0
            while api.poll() is None and expo.poll() is None:
                time.sleep(0.5)
            raise RuntimeError("A service stopped; stopping the other service. See the Expo terminal / API log.")
        except KeyboardInterrupt:
            print("\nStopping Vela...", flush=True)
            return 0
        finally:
            stop(expo)
            stop(api)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"Vela: {error}", file=sys.stderr)
        sys.exit(1)
