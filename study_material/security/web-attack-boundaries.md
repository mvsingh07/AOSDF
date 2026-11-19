---
concepts: [sql-injection, cross-site-scripting, csrf, ssrf]
concept_category: Security
difficulty: intermediate
prerequisites: [authentication, authorization]
interview_angle: >
  Match each untrusted-data sink to its defense: SQL parameters, context-aware output handling,
  CSRF protection for cookie-authenticated writes, and outbound request restrictions for SSRF.
built_at: framework-learning-roadmap
diagram: true
---

# Web Attack Boundaries

## Definition

Injection happens when untrusted data becomes instructions for another interpreter. SQL injection
targets queries; XSS targets the browser's HTML or JavaScript context; SSRF makes the server fetch an
attacker-chosen destination. CSRF uses a victim's browser session to send an unintended state-changing
request. These are different boundaries and need different controls.

## Example

Use parameters for values in SQL, render user text as text, and protect cookie-authenticated writes
with a framework-supported CSRF defense. If the server fetches a user-provided URL, constrain schemes,
destinations, redirects, time, and response size; a simple hostname string check is insufficient.

```python
row = db.execute("SELECT * FROM orders WHERE id = ?", [order_id])
# Keep order_id out of SQL syntax; authorize the returned order separately.
```

## Diagram

```aosdf-diagram
                     ┌──▶ SQL value ──▶ parameterized query
Untrusted input ─────┼──▶ HTML text ─▶ text node / safe rendering
                     └──▶ URL fetch ──▶ destination policy + redirect checks
Cookie session + state-changing request ──▶ CSRF defense
```

## Use It While Building

Trace one input to every place it is interpreted. Name the guard at each sink and write one abuse
test. CORS is a browser read policy, not an authentication, authorization, or CSRF defense.

## Sources

- [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [OWASP CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
