#!/usr/bin/env python3
"""Inactive bounded-job adapter. Product-specific task/pins/permissions never transfer."""
from pathlib import Path


def read_round_sources(channel: Path) -> str:
    """Search live and verbatim history when a caller needs an older numbered round."""
    channel = Path(channel)
    history = channel.parent / "history" / channel.name
    return channel.read_text(encoding="utf-8") + (history.read_text(encoding="utf-8") if history.exists() else "")


def validate_config(config, **kwargs):
    raise ValueError("No project-specific bounded-job contract is installed")


def main():
    raise SystemExit("REFUSED: install and validate a project-specific bounded-job contract first")


if __name__ == "__main__":
    main()
