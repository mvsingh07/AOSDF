#!/usr/bin/env python3
"""Enforced execution scope + environment/action allowlist (P0-8).

Prompt text is NOT a boundary. An action is permitted only if it is on the allowlist, in an
allowed environment, and its target matches no denied pattern. An undeclared action is denied
by default, and no descriptive text ("# safe, read only") can change that — enforcement is by
the action/target/env fields, never by free text. Disposable local resources are explicitly
allowed; shared DB/provider accounts, credential stores/Keychain, publish and deploy are not.
"""
from __future__ import annotations
import fnmatch


class ScopeDenied(RuntimeError):
    pass


def pilot_policy() -> dict:
    """Default deny-by-default policy for a bounded one-task local pilot."""
    return {
        "allowed_actions": [
            "read-file", "write-owned-file", "run-test", "run-build", "run-lint",
            "apply-disposable-dev-migration", "dev-api-smoke", "read-only-provider-lookup",
        ],
        "allowed_envs": ["local", "dev-disposable"],
        "denied_target_patterns": [
            "*prod*", "*production*", "*staging*",
            "*.amazonaws.com*", "*.supabase.co*", "*.supabase.in*", "*zeptomail*", "*zoho*",
            "*keychain*", "*secrets*", "*secret-manager*", "*.env*", "*credential*",
            "git push*", "*deploy*", "*publish*", "*dns*", "*route53*", "*cloudflare*",
        ],
    }


def check_action(policy: dict, action: str, target: str = "", env: str = "local") -> dict:
    if action not in policy.get("allowed_actions", []):
        return {"allowed": False, "reason": f"action {action!r} is not on the allowlist (undeclared -> denied)"}
    if env not in policy.get("allowed_envs", []):
        return {"allowed": False, "reason": f"environment {env!r} not allowed"}
    for pat in policy.get("denied_target_patterns", []):
        if fnmatch.fnmatch(target.lower(), pat.lower()) or pat.strip("*").lower() in target.lower():
            return {"allowed": False, "reason": f"target {target!r} matches denied pattern {pat!r}"}
    return {"allowed": True, "reason": "ok"}


def guard(policy: dict, action: str, target: str = "", env: str = "local") -> None:
    d = check_action(policy, action, target, env)
    if not d["allowed"]:
        raise ScopeDenied(d["reason"])
