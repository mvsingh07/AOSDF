# Compatible change and architecture review

A system is designed for change as well as traffic. During a rollout, old and new API processes, browser clients, and database rows coexist. A migration is safe when each intermediate state works and a rollback is understood.

## Evolve the contract in stages

Suppose documents gain `visibility` (`private` or `team`). First add a nullable database column and make old code ignore it. Deploy new readers that treat a missing value as `private`. Backfill existing rows in bounded batches. Deploy writers that set the field. Only after old writers have left service should you add a strict constraint, if needed. This is **expand, migrate, contract**. Keep access control conservative during the transition: never interpret an absent value as public.

For an HTTP API, adding an optional response field is usually less disruptive than renaming or removing one; test older clients. A new request field should have a safe default or explicit versioning. A URL version is one option, but versioning does not replace compatibility testing. **Semantic versioning** communicates intended compatibility for a versioned public interface or library; it does not automatically govern a continuously deployed internal API or database. Define the contract and deprecation period that clients actually use.

## Review the design against evidence

An architecture review should list the user promise, peak estimate, p99 target, source of truth, authorization point, consistency contract, failure behavior, and rollback. For every cache, replica, or shard, name the measurement that justified it and the new failure mode. Model a primary outage: can reads continue, can edits be honestly accepted, how is failover verified, and what data loss could occur? Model an overloaded database: does the gateway reject excess work, or do retries amplify it? Capture the chosen trade-off and revisit it when traffic or requirements change.

A useful rollout sequence is: add metrics and traces; deploy a compatible schema; release a small percentage of traffic; compare latency, errors, data correctness, and access decisions; expand only if healthy; retain a tested rollback path. A design is not complete if nobody can tell whether it meets its promise.

## Diagram: safe contract evolution

![Old and new clients coexist while a field is added, backfilled, then enforced after old writers are gone.](/learning/scale-design/compatibility.svg)

```aosdf-diagram
Expand schema ──▶ new readers with safe default ──▶ backfill
          └──▶ new writers ──▶ observe ──▶ enforce constraint
```

## Implementation: automate the rollout contract

A migration tool records schema versions, OpenAPI describes the HTTP contract, and metrics show whether a canary behaves as expected. Keep these artifacts in the same review as the code so the rollout sequence is executable, not just a diagram.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![flyway logo](/learning/scale-design/logo-flyway.svg) | [Flyway](https://documentation.red-gate.com/flyway) | Apply ordered, reviewable database migrations. | Use an expand/backfill/contract sequence for live traffic. |
| ![openapiinitiative logo](/learning/scale-design/logo-openapiinitiative.svg) | [OpenAPI Specification](https://spec.openapis.org/oas/) | Describe request fields, responses, and versioned behavior. | Test older clients against the new contract. |
| ![prometheus logo](/learning/scale-design/logo-prometheus.svg) | [Prometheus](https://prometheus.io/docs/introduction/overview/) | Compare canary error rate and p99 with baseline. | Add a rollback trigger tied to user-visible failure. |

A staged change might begin with a Flyway migration `V42__add_visibility.sql` containing `ALTER TABLE documents ADD COLUMN visibility text;`. New readers treat `NULL` as `private`. Backfill in bounded batches; deploy writers that set `visibility`; then add a constraint only after old writers are gone. Update the OpenAPI schema with the new optional field and run compatibility tests against the previous client. During a canary, compare access-denied errors, p99, and inconsistent visibility reports before increasing traffic. Rollback should leave a schema old code can still read.

## Engineering exercise

Write a one-page design review for the shared document library. Include the 1,160-RPS peak assumption, a p99 target, the data and authorization path, cache policy, connection budget, immediate read-after-save behavior, conflict response, two failure drills, and a rollback. Identify which numbers must be replaced with measurements.

## Design review questions

- Why must a database migration work while old API instances still run?
- Is a new URL version enough to guarantee compatibility?
- What does a design review need besides a box-and-arrow diagram?

**Review criteria:** rolling deploys overlap versions; clients and semantics still need tests and a migration path; requirements, evidence, failure contracts, and rollback make the diagram actionable.

## Read further

- [Semantic Versioning specification](https://semver.org/)
- [Google SRE: service level objectives](https://sre.google/sre-book/service-level-objectives/)
- [PostgreSQL: ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)
