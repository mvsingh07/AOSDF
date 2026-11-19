#!/usr/bin/env python3
"""Inactive bounded-job adapter. Product-specific task/pins/permissions never transfer."""
def validate_config(config, **kwargs):
    raise ValueError("No project-specific bounded-job contract is installed")


def main():
    raise SystemExit("REFUSED: install and validate a project-specific bounded-job contract first")


if __name__ == "__main__":
    main()
