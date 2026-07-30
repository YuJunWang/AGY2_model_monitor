import json
import urllib.request
import websocket

# 1. Fetch the debugging URL
req = urllib.request.Request("http://localhost:57297/json/list")
with urllib.request.urlopen(req) as response:
    pages = json.loads(response.read())

ws_url = None
for page in pages:
    if page.get("type") == "page":
        ws_url = page.get("webSocketDebuggerUrl")
        break

if not ws_url:
    print("No inspectable page found.")
    exit(1)

# 2. Connect to the WebSocket
ws = websocket.create_connection(ws_url, suppress_origin=True)

# 3. Send CDP command to evaluate Javascript
# We want to dump window.localStorage and window.sessionStorage
command = {
    "id": 1,
    "method": "Runtime.evaluate",
    "params": {
        "expression": "JSON.stringify({local: localStorage, session: sessionStorage})",
        "returnByValue": True
    }
}

ws.send(json.dumps(command))

# 4. Receive response
result = ws.recv()
print("CDP Result:", result)

ws.close()
