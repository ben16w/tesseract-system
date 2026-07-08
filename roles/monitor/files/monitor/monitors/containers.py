#!/usr/bin/env python3
"""Monitor: Check Docker container stderr for errors.

Writes one file per container with errors to TEMP_DIR.

Environment variables (with defaults):
    POLL_INTERVAL            - minutes to look back (default: 15)
    LOG_FILE                 - path to log file (default: empty, no logging)
    DOCKER_EXCLUDE_CONTAINERS - space-separated container names to skip (default: empty)
    DOCKER_EXCLUDE_PATTERNS  - pipe-separated regex patterns to filter out (default: empty)
"""

import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

TEMP_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else None
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "15"))
LOG_FILE = os.environ.get("LOG_FILE", "")
DOCKER_EXCLUDE_CONTAINERS = os.environ.get("DOCKER_EXCLUDE_CONTAINERS", "").split()
DOCKER_EXCLUDE_PATTERNS = os.environ.get("DOCKER_EXCLUDE_PATTERNS", "")


def log(message):
    """Print a timestamped message to stdout and optionally append to log file."""
    now = datetime.now()
    line = f"{now.strftime('%Y-%m-%d %H:%M:%S')}.{now.microsecond // 1000:03d} {message}"
    print(line)
    if LOG_FILE:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")


def main():
    if TEMP_DIR is None:
        print(f"Usage: {sys.argv[0]} <temp_dir>", file=sys.stderr)
        sys.exit(1)

    try:
        import docker
    except ImportError:
        log("INFO: [docker] python3-docker not installed. Skipping.")
        sys.exit(0)

    try:
        client = docker.from_env()
        client.ping()
    except docker.errors.DockerException:
        log("INFO: [docker] Docker not available. Skipping.")
        sys.exit(0)

    log("INFO: [docker] Checking container stderr for errors.")
    since = datetime.now() - timedelta(minutes=POLL_INTERVAL)

    exclude_re = re.compile(DOCKER_EXCLUDE_PATTERNS) if DOCKER_EXCLUDE_PATTERNS else None

    for container in client.containers.list():
        name = container.name
        if name in DOCKER_EXCLUDE_CONTAINERS:
            continue

        try:
            stderr = container.logs(since=since, stderr=True, stdout=False)
            output = stderr.decode("utf-8", errors="replace").strip()
        except Exception as e:
            log(f"WARNING: [docker] Failed to get logs for {name}: {e}")
            continue

        if not output:
            continue

        if exclude_re:
            lines = [line for line in output.splitlines() if not exclude_re.search(line)]
            output = "\n".join(lines).strip()

        if output:
            log(f"INFO: [docker] Errors found in container: {name}")
            (TEMP_DIR / f"Docker_{name}").write_text(output)

    log("INFO: [docker] Check complete.")


if __name__ == "__main__":
    main()
