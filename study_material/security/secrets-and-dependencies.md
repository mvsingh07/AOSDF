---
concepts: [secrets-management, dependency-supply-chain, secure-deployment]
concept_category: Security
difficulty: fundamental
prerequisites: []
interview_angle: >
  Explain what happens after a credential is exposed: revoke or rotate it, inspect usage,
  remove the leak, and prevent recurrence; deleting a commit alone is insufficient.
built_at: framework-learning-roadmap
diagram: true
---

# Secrets and Dependency Supply Chain

## Definition

A secret is a credential that grants authority, such as an API key or signing key. Store it in a
managed secret store or protected deployment environment, grant the narrowest scope possible, and
rotate it when exposed. Dependencies are executable code in your trust boundary: pin versions with a
lockfile, update deliberately, and review advisories and provenance before release.

## Example

A CI job needs permission to upload one build artifact. Give that job a short-lived credential scoped
to that artifact destination, not a repository-wide personal token. If it leaks in a log, revoke it,
inspect its usage, then remove the logging path.

## Diagram

```aosdf-diagram
┌────────────┐   scoped secret   ┌─────────────┐   signed artifact   ┌──────────┐
│ Secret store│─────────────────▶│ Build job   │─────────────────────▶│ Deploy   │
└────────────┘                  └──────┬──────┘                      └──────────┘
                                      │ pinned dependencies + checks
```

## Use It While Building

Inventory each secret, its owner, scope, storage location, and rotation path. Lock dependencies and
run a supported vulnerability scan in CI. Test that production credentials are absent from browser
bundles and logs.

## Sources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [OpenSSF Scorecard](https://securityscorecards.dev/)
