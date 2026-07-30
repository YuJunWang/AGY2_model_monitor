"""
data_fetcher.py — AGY Fuel Gauge
Credential discovery strategy (in order of priority):
  1. Disk cache  : Load last known port+token, verify they still work → fastest path
  2. Port scan   : Actively probe all local HTTPS ports for the gRPC endpoint
  3. CDP passive : Connect to Electron DevTools, intercept outgoing network traffic → needs user action
"""
import json
import os
import urllib.request
import urllib.error
import websocket
import threading
import ssl
import re
import time

CREDENTIALS_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".credentials_cache.json")
GRPC_PATH = "/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary"


class QuotaFetcher:
    def __init__(self):
        self.port = None
        self.csrf_token = None
        self.lock = threading.Lock()
        self._load_cached_credentials()

    # ── Credential Cache ───────────────────────────────────────────────────────

    def _load_cached_credentials(self):
        """Load last-known port and CSRF token from disk."""
        try:
            if os.path.exists(CREDENTIALS_CACHE):
                with open(CREDENTIALS_CACHE, "r") as f:
                    data = json.load(f)
                self.port = data.get("port")
                self.csrf_token = data.get("csrf_token")
                print(f"[data_fetcher] Loaded cached credentials (port={self.port})")
        except Exception as e:
            print(f"[data_fetcher] Could not load credential cache: {e}")

    def _save_cached_credentials(self):
        """Persist current credentials to disk for faster startup next time."""
        try:
            with open(CREDENTIALS_CACHE, "w") as f:
                json.dump({"port": self.port, "csrf_token": self.csrf_token}, f)
        except Exception as e:
            print(f"[data_fetcher] Could not save credential cache: {e}")

    # ── Strategy 1: Verify Cached Credentials ─────────────────────────────────

    def _verify_credentials(self):
        """Quick test: does the current port+token pair still return data?"""
        if not self.port or not self.csrf_token:
            return False
        try:
            url = f"https://127.0.0.1:{self.port}{GRPC_PATH}"
            headers = {
                "Content-Type": "application/grpc-web+json",
                "Accept": "application/grpc-web+json",
                "x-grpc-web": "1",
                "x-codeium-csrf-token": self.csrf_token,
            }
            req = urllib.request.Request(url, data=b'\x00\x00\x00\x00\x02{}', headers=headers, method="POST")
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, context=ctx, timeout=2) as resp:
                body = resp.read()
                return len(body) > 5
        except Exception:
            return False

    # ── Strategy 2: Active gRPC Port Scan ─────────────────────────────────────

    def _scan_grpc_port(self):
        """
        Probe all local HTTPS ports to find the Antigravity gRPC server.
        Even a 401/403 HTTP error means we found the right port.
        Returns the port as a string, or None.
        """
        import subprocess
        ctx = ssl._create_unverified_context()
        try:
            output = subprocess.check_output(
                "netstat -ano | findstr LISTENING | findstr 127.0.0.1",
                shell=True, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
        except Exception:
            return None

        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            port_str = parts[1].split(":")[-1]
            if not port_str.isdigit():
                continue
            port = int(port_str)
            if port < 10000:  # skip well-known system ports
                continue
            url = f"https://127.0.0.1:{port}{GRPC_PATH}"
            try:
                req = urllib.request.Request(
                    url, data=b'\x00\x00\x00\x00\x02{}',
                    headers={"Content-Type": "application/grpc-web+json", "x-grpc-web": "1"},
                    method="POST"
                )
                with urllib.request.urlopen(req, context=ctx, timeout=0.4) as resp:
                    resp.read()
                    print(f"[data_fetcher] gRPC port found via scan: {port}")
                    return str(port)
            except urllib.error.HTTPError:
                # Any HTTP error (401/403) = right port, wrong/missing auth
                print(f"[data_fetcher] gRPC port found via scan (HTTP error): {port}")
                return str(port)
            except Exception:
                continue
        return None

    # ── Strategy 3: CDP Discovery ──────────────────────────────────────────────

    def _discover_cdp_port(self):
        """Scan netstat to find Antigravity's Electron DevTools (CDP) port."""
        import subprocess
        try:
            output = subprocess.check_output(
                "netstat -ano | findstr LISTENING | findstr 127.0.0.1",
                shell=True, stderr=subprocess.DEVNULL
            ).decode(errors="ignore")
            for line in output.splitlines():
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                port_str = parts[1].split(":")[-1]
                if not port_str.isdigit():
                    continue
                port = int(port_str)
                try:
                    req = urllib.request.Request(f"http://localhost:{port}/json/list")
                    with urllib.request.urlopen(req, timeout=0.5) as response:
                        pages = json.loads(response.read())
                        for page in pages:
                            if page.get("type") == "page" and "webSocketDebuggerUrl" in page:
                                print(f"[data_fetcher] CDP port found: {port}")
                                return port
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def _fetch_credentials_via_cdp(self, cdp_port):
        """
        Connect to Electron DevTools WebSocket and passively intercept
        a LanguageServerService network request to capture port + CSRF token.
        Requires the user to perform an action in Antigravity during the 8s window.
        Returns True if credentials were captured.
        """
        try:
            req = urllib.request.Request(f"http://localhost:{cdp_port}/json/list")
            with urllib.request.urlopen(req, timeout=2) as response:
                pages = json.loads(response.read())
        except Exception as e:
            print(f"[data_fetcher] CDP list failed: {e}")
            return False

        ws_url = None
        for page in pages:
            if page.get("type") == "page":
                ws_url = page.get("webSocketDebuggerUrl")
                break
        if not ws_url:
            return False

        found = []

        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("method") == "Network.requestWillBeSent":
                    url = data["params"]["request"]["url"]
                    if "LanguageServerService" in url:
                        headers = data["params"]["request"]["headers"]
                        if "x-codeium-csrf-token" in headers:
                            match = re.search(r":(\d+)/", url)
                            if match:
                                found.append({
                                    "port": match.group(1),
                                    "token": headers["x-codeium-csrf-token"]
                                })
                                ws.close()
            except Exception:
                pass

        def on_open(ws):
            ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
            # Timeout: give up after 8 seconds
            def timeout_close():
                time.sleep(8)
                try:
                    ws.close()
                except Exception:
                    pass
            threading.Thread(target=timeout_close, daemon=True).start()

        print("[data_fetcher] Waiting for Antigravity network traffic (8s)...")
        ws_app = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
        ws_app.run_forever(suppress_origin=True)

        if found:
            self.port = found[0]["port"]
            self.csrf_token = found[0]["token"]
            return True
        return False

    # ── Master Credential Refresh ──────────────────────────────────────────────

    def _refresh_credentials(self):
        """
        Try all three strategies in order:
        1. Verify cached credentials (instant)
        2. Active gRPC port scan (fast, ~1-2s) — finds port; but needs existing token
        3. CDP passive interception (requires user action in Antigravity)
        """
        # Strategy 1: cached credentials still valid?
        if self._verify_credentials():
            print("[data_fetcher] Cached credentials verified OK.")
            return True

        print("[data_fetcher] Cached credentials invalid or missing. Scanning...")

        # Strategy 2: find gRPC port via active scan
        scanned_port = self._scan_grpc_port()

        # Strategy 3: CDP to get CSRF token (and port as fallback)
        cdp_port = self._discover_cdp_port()
        if cdp_port:
            # If we already have a token, try it with the newly scanned port
            if scanned_port and self.csrf_token:
                self.port = scanned_port
                if self._verify_credentials():
                    print(f"[data_fetcher] Port updated via scan to {scanned_port}, token still valid.")
                    self._save_cached_credentials()
                    return True

            # Fall back to full CDP passive interception
            success = self._fetch_credentials_via_cdp(cdp_port)
            if success:
                # If scan found a different port than what CDP captured, prefer CDP (more authoritative)
                self._save_cached_credentials()
                print(f"[data_fetcher] Credentials captured via CDP. Port={self.port}")
                return True
        else:
            print("[data_fetcher] Antigravity is not running (no CDP port).")

        return False

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_quota(self):
        with self.lock:
            if not self._verify_credentials():
                success = self._refresh_credentials()
                if not success:
                    return None

            url = f"https://127.0.0.1:{self.port}{GRPC_PATH}"
            headers = {
                "Content-Type": "application/grpc-web+json",
                "Accept": "application/grpc-web+json",
                "x-grpc-web": "1",
                "x-codeium-csrf-token": self.csrf_token,
            }
            req = urllib.request.Request(url, data=b'\x00\x00\x00\x00\x02{}', headers=headers, method="POST")
            ctx = ssl._create_unverified_context()
            try:
                with urllib.request.urlopen(req, context=ctx) as response:
                    res_body = response.read().decode("utf-8", errors="ignore")
                    match = re.search(r'({"response":.*?"}})', res_body)
                    if match:
                        return json.loads(match.group(1))
            except Exception as e:
                print(f"[data_fetcher] Quota fetch failed: {e}. Invalidating credentials.")
                self.port = None
                self.csrf_token = None

            return None


# Singleton
fetcher = QuotaFetcher()


def fetch_usage_data():
    from datetime import datetime
    data = fetcher.get_quota()

    result = {
        "gemini": {"5hr_percent": 0, "weekly_percent": 0, "reset_time_5h": "", "reset_time_weekly": ""},
        "external": {"5hr_percent": 0, "weekly_percent": 0, "reset_time_5h": "", "reset_time_weekly": ""},
        "last_updated": datetime.now().strftime("%H:%M:%S"),
    }

    if not data or "response" not in data:
        return result

    for group in data["response"].get("groups", []):
        is_gemini = "Gemini" in group.get("displayName", "")
        for bucket in group.get("buckets", []):
            remaining = bucket.get("remainingFraction", 1)
            remaining_pct = round(remaining * 100, 1)
            used_pct = round((1 - remaining) * 100, 1)
            reset = bucket.get("resetTime", "")

            if bucket.get("window") == "5h":
                key = "gemini" if is_gemini else "external"
                result[key]["5hr_percent"] = remaining_pct
                result[key]["5hr_used"] = used_pct
                result[key]["reset_time_5h"] = reset
            elif bucket.get("window") == "weekly":
                key = "gemini" if is_gemini else "external"
                result[key]["weekly_percent"] = remaining_pct
                result[key]["weekly_used"] = used_pct
                result[key]["reset_time_weekly"] = reset

    import history_logger
    history_logger.log_usage(
        result["gemini"].get("5hr_percent", 100),
        result["external"].get("5hr_percent", 100),
    )

    return result


if __name__ == "__main__":
    print(fetch_usage_data())
