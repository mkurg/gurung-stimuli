"""Keep the loopback-only reference server available independently of the chat."""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parent
APPLICATION = "praat-trial-reference"
LOCAL_HTTP = build_opener(ProxyHandler({}))


def health_matches(payload, root):
    return (isinstance(payload, dict)
            and payload.get("application") == APPLICATION
            and isinstance(payload.get("root"), str)
            and Path(payload["root"]).resolve() == Path(root).resolve())


def read_health(port):
    try:
        with LOCAL_HTTP.open(f"http://127.0.0.1:{port}/api/health", timeout=3) as response:
            return json.load(response)
    except (OSError, URLError, ValueError):
        return None


def server_command(root, executable, port):
    return [str(executable), str(Path(root) / "server.py"), "--port", str(port), "--strict-port"]


def ensure_server(child, root, executable, port, logger, probe=read_health, popen=subprocess.Popen):
    if child is not None and child.poll() is None:
        return child
    if child is not None:
        logger.warning("Server exited with code %s; checking before restart.", child.returncode)
    health = probe(port)
    if health_matches(health, root):
        return None
    if health is not None:
        logger.warning("Port %s belongs to another application or library; leaving it untouched.", port)
        return None
    with (Path(root) / "service_server.log").open("ab") as output:
        child = popen(server_command(root, executable, port), cwd=root,
                      stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                      close_fds=True)
    logger.info("Started server pid %s on http://127.0.0.1:%s", child.pid, port)
    return child


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.interval < 1:
        parser.error("Choose a valid port and an interval of at least one second.")
    logger = logging.getLogger("reference-service")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(ROOT / "service_runner.log", maxBytes=1_000_000, backupCount=2)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.info("Supervisor started, pid %s.", os.getpid())
    child = None
    try:
        while True:
            try:
                child = ensure_server(child, ROOT, sys.executable, args.port, logger)
            except OSError:
                logger.exception("Could not start the server; will retry.")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Supervisor interrupted.")
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            child.wait(timeout=10)


if __name__ == "__main__":
    main()
