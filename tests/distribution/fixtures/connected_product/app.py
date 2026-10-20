from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

from domain import validate_quantity


ROOT = Path(__file__).resolve().parent


def connect(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def initialize(database: Path) -> None:
    with closing(connect(database)) as connection:
        with connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS items ("
                "id INTEGER PRIMARY KEY, quantity INTEGER NOT NULL CHECK(quantity >= 0))"
            )


class Handler(BaseHTTPRequestHandler):
    database: Path
    identity: dict

    def send_json(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        route = urlsplit(self.path).path
        files = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/history": ("history.html", "text/html; charset=utf-8"),
            "/shared.css": ("shared.css", "text/css; charset=utf-8"),
            "/ui.js": ("ui.js", "text/javascript; charset=utf-8"),
        }
        if route in files:
            filename, content_type = files[route]
            body = (ROOT / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if route == "/health":
            with closing(connect(self.database)) as connection:
                count = connection.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            self.send_json(200, {"ready": True, "storage": "sqlite", "item_count": count,
                                 "identity": self.identity})
            return
        if route == "/api/items":
            with closing(connect(self.database)) as connection:
                rows = connection.execute("SELECT id, quantity FROM items ORDER BY id").fetchall()
            self.send_json(200, {"items": [dict(row) for row in rows]})
            return
        self.send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/items":
            self.send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Request body must be between 1 and 4096 bytes")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Request body must be an object")
            quantity = validate_quantity(payload.get("quantity"))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
            self.send_json(422, {"error": str(error)})
            return
        try:
            with closing(connect(self.database)) as connection:
                with connection:
                    cursor = connection.execute("INSERT INTO items(quantity) VALUES (?)", (quantity,))
                    item = {"id": cursor.lastrowid, "quantity": quantity}
        except sqlite3.IntegrityError:
            self.send_json(422, {"error": "Storage rejected an invalid quantity"})
            return
        self.send_json(201, item)

    def log_message(self, format: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), format % args), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--port-file", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    initialize(args.database)
    Handler.database = args.database.resolve()
    Handler.identity = {
        "pid": os.getpid(), "root": str(ROOT), "database": str(Handler.database),
        "source": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                   for name in ("app.py", "domain.py", "ui.js", "index.html", "history.html", "shared.css")},
    }
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    address = {"host": "127.0.0.1", "port": server.server_address[1], "pid": os.getpid()}
    args.port_file.write_text(json.dumps(address), encoding="utf-8")
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
