#!/usr/bin/env python3
"""notify.py — one pluggable notifier for the automation runtime.

Order of delivery, best-effort, never raising:
  1. Slack  — iff config/slack.json exists with {"webhook_url": "https://hooks.slack.com/..."}.
              This is the founder's channel for "a simple question or confirmation" (manual_detector):
              the question goes to Slack and is answered from Slack only. The webhook URL is a SECRET
              the founder supplies; it is NOT committed here (only slack.json.example is).
  2. macOS banner — a desktop notification via osascript (dev convenience when no Slack).
  3. stdout  — always, so a notification is never silently lost (and so it shows in the daemon log).

A webhook URL is a credential: it lives only in config/slack.json (gitignored by convention),
never in code, never echoed to a log. notify() prints the message text, never the URL.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(HERE, "config")
SLACK_CFG = os.path.join(CONFIG_DIR, "slack.json")


def slack_configured() -> bool:
    try:
        with open(SLACK_CFG, "r", encoding="utf-8") as fh:
            return bool(json.load(fh).get("webhook_url"))
    except (OSError, ValueError):
        return False


def _slack_webhook() -> str | None:
    try:
        with open(SLACK_CFG, "r", encoding="utf-8") as fh:
            url = json.load(fh).get("webhook_url")
            return url if isinstance(url, str) and url.startswith("https://hooks.slack.com/") else None
    except (OSError, ValueError):
        return None


def _post_slack(text: str) -> bool:
    url = _slack_webhook()
    if not url:
        return False
    import urllib.request
    import urllib.error
    payload = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError, ValueError):
        return False


def _macos_banner(title: str, text: str) -> bool:
    if sys.platform != "darwin":
        return False
    try:
        import subprocess
        # Keep text single-line and quote-safe for osascript.
        safe = text.replace('"', "'").replace("\n", " ")
        subprocess.run(
            ["osascript", "-e", f'display notification "{safe}" with title "{title}"'],
            check=False, capture_output=True, timeout=5,
        )
        return True
    except Exception:
        return False


def notify(text: str, *, title: str = "Example Project automation", level: str = "info") -> dict:
    """Send a notification through the best available channel(s). Returns which fired.

    `level` is a tag ("info" | "action" | "question" | "escalate") prepended to the Slack/stdout
    line so the founder can triage; it changes no behaviour here.
    """
    tag = {"info": "", "action": "🔧 ", "question": "❓ ", "escalate": "🚨 "}.get(level, "")
    line = f"{tag}{text}"
    fired = {"slack": False, "macos": False, "stdout": True, "level": level}
    fired["slack"] = _post_slack(f"*{title}* — {line}") if slack_configured() else False
    if not fired["slack"]:
        fired["macos"] = _macos_banner(title, line)
    # stdout always, so the daemon log and any watching terminal carry it too.
    where = "slack" if fired["slack"] else ("macos" if fired["macos"] else "stdout-only")
    print(f"[notify:{where}] {title}: {line}", flush=True)
    return fired


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Send a test notification through the runtime notifier.")
    ap.add_argument("message", nargs="?", default="test notification from notify.py")
    ap.add_argument("--title", default="Example Project automation")
    ap.add_argument("--level", default="info", choices=["info", "action", "question", "escalate"])
    a = ap.parse_args()
    print(f"slack configured: {slack_configured()}")
    notify(a.message, title=a.title, level=a.level)
