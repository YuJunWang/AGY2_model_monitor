"""
data_fetcher.py — AGY Fuel Gauge
100% Deterministic & Instant Credential Discovery Strategy:
  1. Find Antigravity.exe PIDs via tasklist.
  2. Find listening port for Antigravity.exe via netstat (CDP port).
  3. Compute gRPC port = CDP port + 1.
  4. Extract latest --csrf_token directly from Antigravity's main.log.
  5. Query RetrieveUserQuotaSummary via gRPC-Web HTTPS POST.
"""
import json
import os
import re
import ssl
import subprocess
import urllib.request

LOG_DIR = os.path.expanduser(r"~\AppData\Roaming\Antigravity\logs")
GRPC_PATH = "/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary"


class QuotaFetcher:
    def __init__(self):
        self.cdp_port = None
        self.grpc_port = None
        self.csrf_token = None

    def _find_antigravity_ports(self):
        """Find gRPC port by directly querying language_server.exe's listening ports."""
        try:
            # Step 1: Get language_server.exe PIDs
            ls_out = subprocess.check_output(
                'tasklist /FI "IMAGENAME eq language_server.exe"', shell=True
            ).decode(errors='ignore')
            ls_pids = set()
            for line in ls_out.splitlines():
                if 'language_server.exe' in line:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        ls_pids.add(parts[1])

            if not ls_pids:
                print("[data_fetcher] language_server.exe not found.")
                return None, None

            # Step 2: Find all ports listening under language_server PIDs
            net_out = subprocess.check_output('netstat -ano', shell=True).decode(errors='ignore')
            candidate_ports = []
            for line in net_out.splitlines():
                if 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5 and parts[-1] in ls_pids:
                        port_str = parts[1].split(':')[-1]
                        if port_str.isdigit():
                            candidate_ports.append(int(port_str))

            if not candidate_ports:
                print("[data_fetcher] No listening ports found for language_server.exe.")
                return None, None

            # Step 3: Try each candidate port with an HTTPS gRPC-Web probe
            # The correct port will accept the connection (even if it returns an error body)
            csrf_token = self._extract_csrf_token()
            if not csrf_token:
                # Without token we can't probe; just return the lowest port as best guess
                candidate_ports.sort()
                return None, candidate_ports[0]

            ctx = __import__('ssl')._create_unverified_context()
            for port in sorted(candidate_ports):
                try:
                    probe_url = f"https://127.0.0.1:{port}{GRPC_PATH}"
                    probe_req = urllib.request.Request(
                        probe_url,
                        data=b'\x00\x00\x00\x00\x02{}',
                        headers={
                            "Content-Type": "application/grpc-web+json",
                            "x-grpc-web": "1",
                            "x-codeium-csrf-token": csrf_token,
                        },
                        method="POST"
                    )
                    with urllib.request.urlopen(probe_req, context=ctx, timeout=2) as resp:
                        resp.read()  # If we get any response, this is the gRPC port
                        return None, port  # cdp_port not needed; grpc_port found
                except urllib.error.HTTPError:
                    return None, port  # HTTP error = server responded = correct port
                except Exception:
                    continue  # Connection refused or timeout = wrong port

        except Exception as e:
            print(f"[data_fetcher] Error discovering ports: {e}")

        return None, None


    def _extract_csrf_token(self):
        """Extract the latest --csrf_token from Antigravity's main.log."""
        main_log = os.path.join(LOG_DIR, "main.log")
        if not os.path.exists(main_log):
            # Fallback search in LOG_DIR
            for root, _, files in os.walk(LOG_DIR):
                if "main.log" in files:
                    main_log = os.path.join(root, "main.log")
                    break

        if not os.path.exists(main_log):
            return None

        try:
            with open(main_log, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                tokens = re.findall(r'--csrf_token\s+([a-f0-9\-]+)', content)
                if tokens:
                    return tokens[-1]  # Return most recently logged token
        except Exception as e:
            print(f"[data_fetcher] Error reading main.log for token: {e}")

        return None

    def get_quota(self):
        # 1. Discover Ports
        self.cdp_port, self.grpc_port = self._find_antigravity_ports()
        if not self.grpc_port:
            print("[data_fetcher] Could not locate Antigravity gRPC port.")
            return None

        # 2. Discover CSRF Token
        self.csrf_token = self._extract_csrf_token()
        if not self.csrf_token:
            print("[data_fetcher] Could not locate CSRF token in main.log.")
            return None

        # 3. Query gRPC Endpoint
        url = f"https://127.0.0.1:{self.grpc_port}{GRPC_PATH}"
        headers = {
            "Content-Type": "application/grpc-web+json",
            "Accept": "application/grpc-web+json",
            "x-grpc-web": "1",
            "x-codeium-csrf-token": self.csrf_token,
        }
        body = b'\x00\x00\x00\x00\x02{}'

        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
                res_body = resp.read().decode("utf-8", errors="ignore")
                match = re.search(r'({"response":.*?"}})', res_body)
                if match:
                    return json.loads(match.group(1))
        except Exception as e:
            print(f"[data_fetcher] Quota query failed on port {self.grpc_port}: {e}")

        return None


# Singleton instance
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



