#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from reviews import append_review, delete_review as delete_review_entry, load_reviews


APP_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = APP_DIR.parent
DEFAULT_SITE_ROOT = WORKSPACE_DIR / "docs"
DEFAULT_REVIEWS_FILE = WORKSPACE_DIR / "reviews.json"


class ReviewSiteHandler(SimpleHTTPRequestHandler):
    site_root: Path
    reviews_file: Path

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        clean = parsed.path
        if clean == "/":
            clean = "/index.html"
        clean = clean.lstrip("/")
        return str((self.site_root / clean).resolve())

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/reviews":
            self.send_json(load_reviews(self.reviews_file))
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/reviews":
            self.save_review()
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown endpoint.")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/reviews":
            self.delete_saved_review()
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Unknown endpoint.")

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        super().end_headers()

    def send_json(self, payload: object) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self, max_bytes: int = 12000) -> dict[str, object] | None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Invalid content length.")
            return None

        if content_length <= 0 or content_length > max_bytes:
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Invalid request body size.")
            return None

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Request body must be valid JSON.")
            return None

        if not isinstance(payload, dict):
            self.send_error_json(HTTPStatus.BAD_REQUEST, "Request body must be an object.")
            return None
        return payload

    def save_review(self) -> None:
        payload = self.read_json_body()
        if payload is None:
            return

        try:
            result = append_review(self.reviews_file, payload)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except OSError as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not save review: {exc}")
            return

        self.send_json(result)

    def delete_saved_review(self) -> None:
        payload = self.read_json_body()
        if payload is None:
            return

        try:
            result = delete_review_entry(self.reviews_file, payload)
        except ValueError as exc:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        except OSError as exc:
            self.send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not delete review: {exc}")
            return

        self.send_json(result)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the Gurung viewer and collect picture reviews.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host, default 127.0.0.1")
    parser.add_argument("--port", type=int, default=8780, help="Bind port, default 8780")
    parser.add_argument(
        "--site-root",
        default=os.environ.get("GURUNG_SITE_ROOT", str(DEFAULT_SITE_ROOT)),
        help="Static site root, default docs",
    )
    parser.add_argument(
        "--reviews-file",
        default=os.environ.get("GURUNG_REVIEWS_FILE", str(DEFAULT_REVIEWS_FILE)),
        help="JSON file where reviews are stored",
    )
    args = parser.parse_args()

    site_root = Path(args.site_root).expanduser().resolve()
    reviews_file = Path(args.reviews_file).expanduser().resolve()
    if not site_root.is_dir():
        raise FileNotFoundError(f"Site root does not exist: {site_root}")

    ReviewSiteHandler.site_root = site_root
    ReviewSiteHandler.reviews_file = reviews_file

    server = ThreadingHTTPServer((args.host, args.port), ReviewSiteHandler)
    print(f"Gurung review site: http://{args.host}:{args.port}")
    print(f"Site root: {site_root}")
    print(f"Reviews file: {reviews_file}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
