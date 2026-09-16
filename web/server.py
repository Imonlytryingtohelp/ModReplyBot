import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

WEB_ROOT = Path(__file__).parent
LOG_PATH = Path(os.environ.get("MRB_INTERACTIONS_LOG", WEB_ROOT.parent / "DB" / "moderator_interactions.jsonl"))
HOST = os.environ.get("MRB_WEB_HOST", "0.0.0.0")
PORT = int(os.environ.get("MRB_WEB_PORT", "8080"))


def read_interactions():
    records = []
    if not LOG_PATH.exists():
        return records
    with LOG_PATH.open("r", encoding="utf-8") as log_file:
        for line_number, line in enumerate(log_file, 1):
            try:
                record = json.loads(line)
                if isinstance(record, dict):
                    records.append(record)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON on line {line_number}.")
    return records


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlparse(self.path)
        if request.path == "/api/interactions":
            self.send_json(read_interactions())
            return
        if request.path == "/" or request.path == "/index.html":
            self.send_file(WEB_ROOT / "index.html")
            return
        self.send_error(404)

    def send_json(self, value):
        payload = json.dumps(value, ensure_ascii=True).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_file(self, path):
        if not path.is_file() or path.parent != WEB_ROOT:
            self.send_error(404)
            return
        payload = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "text/plain")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format_string, *args):
        print(f"[WEB] {self.address_string()} - {format_string % args}")


if __name__ == "__main__":
    print(f"Serving moderator dashboard on http://{HOST}:{PORT}")
    print(f"Reading interaction log from {LOG_PATH}")
    ThreadingHTTPServer((HOST, PORT), DashboardHandler).serve_forever()
