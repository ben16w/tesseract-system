#!/usr/bin/env python3
"""Monitor orchestrator - scans monitors/ directory and sends email alerts."""

import os
import shutil
import smtplib
import socket
import subprocess
import sys
import tempfile
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path


def parse_config(path):
    """Parse a KEY=value config file into a dict."""
    config = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                config[key.strip()] = value.strip()
    return config


def log(message, log_file):
    """Append a timestamped message to the log file."""
    if not log_file:
        return
    timestamp = datetime.now().strftime("%F %T.%3N")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} {message}\n")


def send_email(config, subject, body):
    """Send an email via SMTP."""
    hostname = socket.gethostname()
    full_subject = f"[{hostname}] {subject}"

    msg = MIMEText(body)
    msg["To"] = config["EMAIL_TO"]
    msg["From"] = config["EMAIL_FROM"]
    msg["Subject"] = full_subject

    port = int(config["EMAIL_PORT"])
    if port == 465:
        server = smtplib.SMTP_SSL(config["EMAIL_HOST"], port)
    else:
        server = smtplib.SMTP(config["EMAIL_HOST"], port)
        server.starttls()

    server.login(config["EMAIL_FROM"], config["EMAIL_PASSWORD"])
    server.sendmail(config["EMAIL_FROM"], config["EMAIL_TO"], msg.as_string())
    server.quit()


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"Usage: {sys.argv[0]} <config_file> [--dry]")
        sys.exit(0)

    if os.geteuid() != 0:
        print("ERROR: Must be run as root.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <config_file> [--dry]", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[1]
    dry_run = "--dry" in sys.argv or "-d" in sys.argv

    config = parse_config(config_path)
    log_file = config.get("LOG_FILE", "")

    if dry_run:
        log("INFO: Dry run enabled.", log_file)

    tmp_dir = tempfile.mkdtemp(prefix="monitor_")
    try:
        monitors_dir = Path(__file__).resolve().parent / "monitors"
        if not monitors_dir.is_dir():
            log("ERROR: Monitors directory not found.", log_file)
            sys.exit(1)

        scripts = sorted(
            p
            for p in monitors_dir.iterdir()
            if p.suffix in (".sh", ".py") and p.is_file()
        )

        log(f"INFO: Running {len(scripts)} monitor(s).", log_file)

        env = {**os.environ, **config}
        for script in scripts:
            log(f"INFO: Running {script.name}.", log_file)
            result = subprocess.run(
                [str(script), tmp_dir],
                env=env,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                log(
                    f"WARNING: {script.name} exited with code {result.returncode}.",
                    log_file,
                )
                if result.stderr:
                    log(f"  stderr: {result.stderr.strip()}", log_file)

        # Process email files
        tmp_path = Path(tmp_dir)
        email_files = sorted(f for f in tmp_path.iterdir() if f.is_file())

        if email_files:
            log(f"INFO: {len(email_files)} email(s) to send.", log_file)
            for email_file in email_files:
                subject = email_file.stem.replace("_", " ")
                body = email_file.read_text()
                if dry_run:
                    log(f"INFO: Dry run - would send: {subject}", log_file)
                else:
                    try:
                        send_email(config, subject, body)
                        log(f"INFO: Sent email: {subject}", log_file)
                    except Exception as e:
                        log(f"ERROR: Failed to send '{subject}': {e}", log_file)
        else:
            log("INFO: No errors found.", log_file)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
