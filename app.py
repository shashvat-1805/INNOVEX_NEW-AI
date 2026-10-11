"""INNOVEX local demo server. Uses only Python standard library; Node.js/npm not required."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, os, sqlite3, threading

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT
DATA = ROOT / "data"
DB_PATH = DATA / "innovex.sqlite3"
PORT = int(os.environ.get("PORT", "3000"))
DB_LOCK = threading.Lock()

DATA.mkdir(exist_ok=True)

def db_connect():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con

with db_connect() as con:
    con.execute("CREATE TABLE IF NOT EXISTS demo_workspace (id INTEGER PRIMARY KEY CHECK(id=1), state_json TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self.send_json(200, {"ok": True, "service": "INNOVEX Python local server"})
        if path == "/api/demo/state":
            with DB_LOCK, db_connect() as con:
                row = con.execute("SELECT state_json, version, updated_at FROM demo_workspace WHERE id=1").fetchone()
            if row is None:
                return self.send_json(200, {"state": None, "version": 0})
            try:
                state = json.loads(row["state_json"])
            except json.JSONDecodeError:
                return self.send_json(500, {"error": "Saved demo state is invalid JSON"})
            return self.send_json(200, {"state": state, "version": row["version"], "updatedAt": row["updated_at"]})
        if path.startswith("/api/"):
            return self.send_json(404, {"error": "API endpoint not found"})
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_PUT(self):
        path = urlparse(self.path).path
        if path != "/api/demo/state":
            return self.send_json(404, {"error": "API endpoint not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 2_500_000:
                return self.send_json(413, {"error": "Demo workspace is too large"})
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return self.send_json(400, {"error": "Request body must be valid JSON"})
        if not isinstance(data, dict) or not isinstance(data.get("ch"), list) or not isinstance(data.get("st"), list):
            return self.send_json(400, {"error": "State must contain challenge and startup arrays"})
        if len(data["ch"]) > 2000 or len(data["st"]) > 2000:
            return self.send_json(413, {"error": "Demo workspace has too many records"})
        state_json = json.dumps({"ch": data["ch"], "st": data["st"]}, ensure_ascii=False, separators=(",", ":"))
        if len(state_json.encode("utf-8")) > 2_500_000:
            return self.send_json(413, {"error": "Demo workspace is too large"})
        with DB_LOCK, db_connect() as con:
            row = con.execute("SELECT version FROM demo_workspace WHERE id=1").fetchone()
            current = row["version"] if row else 0
            try:
                incoming = int(data.get("v", 0))
            except (ValueError, TypeError):
                incoming = 0
            version = max(current + 1, incoming)
            con.execute("INSERT INTO demo_workspace(id,state_json,version,updated_at) VALUES(1,?,?,CURRENT_TIMESTAMP) ON CONFLICT(id) DO UPDATE SET state_json=excluded.state_json, version=excluded.version, updated_at=CURRENT_TIMESTAMP", (state_json, version))
        return self.send_json(200, {"ok": True, "version": version})

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"INNOVEX is running at http://127.0.0.1:{PORT}")
    print("Python standard library only — Node.js and npm are not required.")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping INNOVEX...")
    finally:
        server.server_close()
