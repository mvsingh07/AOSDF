---
concepts: [clock-skew, logical-clocks, vector-clocks]
concept_category: Distributed Systems
difficulty: advanced
prerequisites: []
interview_angle: >
  Be ready to explain why "just compare timestamps" is unsafe across machines (clock skew), and what
  a logical clock gives you instead — ordering of events, not wall-clock time itself.
built_at: L6-T1
diagram: false
---

# Clock Skew & Distributed Time

## Definition

- **Clock skew:** physical clocks on different machines drift apart over time (crystal oscillators aren't
  perfectly synchronized) — even with NTP correction, machines rarely agree on the exact time to better
  than tens of milliseconds. This makes naive "compare two timestamps from different machines" logic
  unreliable for ordering events precisely.
- **Logical clocks (Lamport timestamps):** instead of relying on wall-clock time, each event gets a
  counter that increments locally and is included in every message sent; a receiver bumps its own counter
  to be greater than the received value. This gives a **happens-before** ordering — if event A causally
  influenced event B, A's logical timestamp is guaranteed to be smaller — without needing synchronized
  clocks at all.
- **Vector clocks:** an extension of Lamport timestamps that can also detect **concurrent** events (two
  events neither of which causally influenced the other) — a Lamport timestamp alone can't distinguish
  "actually happened first" from "just got a smaller arbitrary counter."

## Example

```
Node A: event a1 (clock=1) ──sends message, clock=2──▶ Node B: receives, bumps clock to max(local, 2)+1 = 3
Node B: event b1 now has clock=3 — guaranteed greater than a1's clock=1, correctly reflecting
        that a1 causally happened before b1, regardless of what each machine's physical clock said
```

## Why This Matters in Practice

Google's Spanner database famously addresses clock skew directly with **TrueTime** — GPS and atomic
clocks bound the maximum clock uncertainty to a known window, and the database deliberately *waits out*
that uncertainty window before committing a transaction, trading a small amount of latency for a real
global ordering guarantee. Most systems can't afford that hardware, which is exactly why logical/vector
clocks (a purely algorithmic solution, no special hardware) remain the standard tool for ordering events
correctly across an ordinary distributed system.
