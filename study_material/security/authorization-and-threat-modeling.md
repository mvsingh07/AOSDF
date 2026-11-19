---
concepts: [threat-modeling, least-privilege, object-level-authorization]
concept_category: Security
difficulty: fundamental
prerequisites: [authentication, authorization]
interview_angle: >
  Explain why a valid session does not permit reading another user's object and show where the
  object-specific check belongs.
built_at: framework-learning-roadmap
diagram: true
---

# Threat Modeling, Least Privilege, and Object Authorization

## Definition

A threat model is a short inventory of what needs protection, where untrusted input enters, who could
abuse it, and what controls stop that abuse. Least privilege gives a user, service, or agent only the
permissions needed for its task. Authorization must check the requested *object and action* on every
request; a login only establishes an identity.

## Example

A signed-in user requests `GET /api/invoices/42`. The API loads invoice 42, then verifies its tenant is
in the user's allowed tenant set before returning any invoice data. Test with an invoice owned by a
different tenant; a `403` or privacy-preserving `404` is the expected result.

```python
def read_invoice(user, invoice_id):
    invoice = invoices.get(invoice_id)
    if invoice is None or invoice.tenant_id not in user.allowed_tenant_ids:
        raise NotFound()
    return invoice
```

## Diagram

```aosdf-diagram
┌────────┐    ┌──────────────┐    ┌─────────────────┐    ┌─────────────┐
│ Caller │───▶│ Authenticate │───▶│ Authorize object│───▶│ Read/write  │
└────────┘    └──────────────┘    └─────────────────┘    └─────────────┘
                         valid session ≠ access to every object
```

## Use It While Building

For each feature, list the asset, callers, actions, and one cross-user or cross-tenant abuse case.
Write a denied-case test alongside the happy path. Never rely on an unguessable ID or a disabled UI
button as the authorization control.

## Sources

- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [NIST Secure Software Development Framework](https://csrc.nist.gov/projects/ssdf)
