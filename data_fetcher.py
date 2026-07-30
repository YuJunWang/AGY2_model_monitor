import json
import urllib.request
import websocket
import threading
import ssl
import re

class QuotaFetcher:
    def __init__(self):
        self.port = None
        self.csrf_token = None
        self.lock = threading.Lock()
        
    def _fetch_credentials_via_cdp(self):
        """Uses CDP to silently extract the dynamic port and CSRF token from background traffic."""
        try:
            req = urllib.request.Request("http://localhost:57297/json/list")
            with urllib.request.urlopen(req) as response:
                pages = json.loads(response.read())
        except Exception as e:
            print("Could not connect to CDP:", e)
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
            data = json.loads(message)
            if data.get("method") == "Network.requestWillBeSent":
                url = data["params"]["request"]["url"]
                if "LanguageServerService" in url:
                    headers = data["params"]["request"]["headers"]
                    if "x-codeium-csrf-token" in headers:
                        # Extract port from URL (e.g. https://127.0.0.1:57298/...)
                        match = re.search(r':(\d+)/', url)
                        if match:
                            found.append({
                                "port": match.group(1),
                                "token": headers["x-codeium-csrf-token"]
                            })
                            ws.close()

        def on_open(ws):
            ws.send(json.dumps({"id": 1, "method": "Network.enable"}))

        ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
        ws.run_forever(suppress_origin=True)

        if found:
            self.port = found[0]["port"]
            self.csrf_token = found[0]["token"]
            return True
        return False

    def get_quota(self):
        with self.lock:
            if not self.port or not self.csrf_token:
                success = self._fetch_credentials_via_cdp()
                if not success:
                    return None

            url = f"https://127.0.0.1:{self.port}/exa.language_server_pb.LanguageServerService/RetrieveUserQuotaSummary"
            headers = {
                "Content-Type": "application/grpc-web+json",
                "Accept": "application/grpc-web+json",
                "x-grpc-web": "1",
                "x-codeium-csrf-token": self.csrf_token
            }
            body = b'\x00\x00\x00\x00\x02{}'
            
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            context = ssl._create_unverified_context()
            
            try:
                with urllib.request.urlopen(req, context=context) as response:
                    res_body = response.read().decode('utf-8', errors='ignore')
                    # Parse gRPC-Web JSON payload
                    match = re.search(r'({"response":.*?"}})', res_body)
                    if match:
                        return json.loads(match.group(1))
            except Exception as e:
                # Token or port might have expired/changed, reset them
                self.port = None
                self.csrf_token = None
                
            return None

# Singleton instance
fetcher = QuotaFetcher()

def fetch_usage_data():
    from datetime import datetime
    data = fetcher.get_quota()
    
    # Default fallback empty structure
    result = {
        "gemini": {"5hr_percent": 0, "weekly_percent": 0, "reset_time_5h": "", "reset_time_weekly": ""},
        "external": {"5hr_percent": 0, "weekly_percent": 0, "reset_time_5h": "", "reset_time_weekly": ""},
        "last_updated": datetime.now().strftime("%H:%M:%S")
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
            if reset:
                try:
                    # Convert '2026-07-30T08:38:06Z' to '08:38'
                    dt = datetime.strptime(reset, "%Y-%m-%dT%H:%M:%SZ")
                    reset = dt.strftime("%m/%d %H:%M")
                except:
                    pass
                    
            if bucket.get("window") == "5h":
                if is_gemini:
                    result["gemini"]["5hr_percent"] = remaining_pct
                    result["gemini"]["5hr_used"] = used_pct
                    result["gemini"]["reset_time_5h"] = reset
                else:
                    result["external"]["5hr_percent"] = remaining_pct
                    result["external"]["5hr_used"] = used_pct
                    result["external"]["reset_time_5h"] = reset
            elif bucket.get("window") == "weekly":
                if is_gemini:
                    result["gemini"]["weekly_percent"] = remaining_pct
                    result["gemini"]["weekly_used"] = used_pct
                    result["gemini"]["reset_time_weekly"] = reset
                else:
                    result["external"]["weekly_percent"] = remaining_pct
                    result["external"]["weekly_used"] = used_pct
                    result["external"]["reset_time_weekly"] = reset
                    
    return result

if __name__ == "__main__":
    print(fetch_usage_data())
