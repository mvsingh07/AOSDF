---
concepts: [back-of-envelope-estimation, capacity-estimation]
concept_category: System Design Process
difficulty: fundamental
prerequisites: []
interview_angle: >
  Be ready to derive QPS, storage, and bandwidth from a handful of stated assumptions in a couple of
  minutes — the point isn't precision, it's proving the design's bottleneck is where you think it is
  before you design around it.
built_at: L6-T1
diagram: false
---

# Back-of-Envelope Estimation

## Definition

**Back-of-envelope estimation** is the practice of sanity-checking a system's scale — requests per second,
storage growth, bandwidth — using rough, round-number arithmetic from a few stated assumptions, before
committing to a design. It's not about precise numbers; it's about knowing whether you're building for
thousands or billions of anything, since that changes which patterns in this corpus (a single database vs.
sharding, a single cache node vs. consistent hashing) are even relevant.

Common reference numbers worth having memorized: 1 day ≈ 86,400 seconds (round to ~100,000 for quick
mental math); 1 million requests/day ≈ 12 QPS average (but design for peak, often 2-10x average).

## Example

"Design a URL shortener for 100M new URLs/month, read:write ratio 10:1."

```
Writes:  100,000,000 / month ÷ (30 × 86,400 s/month) ≈ 40 writes/sec average
Reads:   40 writes/sec × 10                          ≈ 400 reads/sec average
Storage: 100M URLs/month × 12 months × 5 years × ~500 bytes/record ≈ 3 TB over 5 years
```

That last number is the one that matters: 3 TB comfortably fits on a single well-provisioned database with
room to grow — it tells you sharding (`sharding-and-rebalancing.md`) is *not* yet justified for this
specific problem, before you've spent any design time on it.
