---
concepts: [authentication, authorization, oauth2, jwt]
concept_category: Security
difficulty: intermediate
prerequisites: []
interview_angle: >
  The single most common interview trap here is conflating authentication and authorization — be
  ready to give one sentence distinguishing them before anything else, and know that a JWT is a
  token *format*, not an authentication *protocol* by itself.
built_at: L6-T1
diagram: false
---

# Authentication vs. Authorization, OAuth2, JWT

## Definition

- **Authentication (AuthN):** proving *who you are* — a login with a password, a passkey, an SSO flow.
- **Authorization (AuthZ):** determining *what you're allowed to do*, once identity is established — a
  logged-in user might still be forbidden from an admin-only action.
- **OAuth2:** a protocol for delegated authorization — letting a third-party app act on a user's behalf
  against a resource server, without ever seeing the user's actual password (the "Sign in with Google"
  flow). Often conflated with authentication, but it's fundamentally an authorization protocol; **OpenID
  Connect** is the identity layer built on top of it that actually handles authentication.
- **JWT (JSON Web Token):** a signed, self-contained token format encoding claims (user ID, roles,
  expiry) — a server can verify it's untampered via its signature without a database lookup, at the cost
  that a JWT can't be easily revoked before it expires (its claims are baked in until then).

## Example

```
JWT structure: header.payload.signature
{"alg":"HS256"}.{"sub":"user_42","role":"admin","exp":1735689600}.<signature>
```

Authorization check using that token's claims, independent of how the user authenticated:

```python
def require_admin(request):
    claims = verify_jwt(request.headers["Authorization"])
    if claims["role"] != "admin":
        raise Forbidden()  # authenticated, but not authorized for this action
```

## Where AOSDF Draws This Boundary Deliberately

`AOSDF-Hosting`'s dashboard is explicitly localhost-only with **no authentication at all** (`OD-H9`) —
a deliberate MVP scope decision (single operator, no remote exposure), not an oversight. The moment that
dashboard is exposed beyond localhost, both authentication (who's logging in) and authorization (what a
given logged-in user can trigger — e.g. can every user delete a registered product?) become required, not
optional.
