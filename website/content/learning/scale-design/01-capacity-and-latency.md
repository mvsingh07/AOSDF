# Capacity, throughput, and tail latency

**Throughput** is work completed per unit time; **latency** is elapsed time for one request. More throughput does not imply a good user experience if the slowest requests become much slower. A capacity estimate is an initial model to test, not a procurement order.

## Calculate from demand to peak

Suppose the library receives **10 million document opens/day** and **100,000 edits/day**. Average opens are `10,000,000 / 86,400 ≈ 116 requests/second`. If the busiest period is ten times the average, plan an initial **1,160 open requests/second**, plus edits and search. State the multiplier as an assumption and verify it from traffic telemetry. A 2× seasonal event or retry storm may require a separate scenario.

If one open occupies an API worker for 120 ms, Little's law gives roughly `1,160 × 0.120 ≈ 139` concurrent in-flight opens at that peak. This is a first concurrency estimate; queues, I/O wait, connection pools, and burst shape still matter. If each open causes three database queries, the database sees roughly 3,480 queries/second before cache hits. Measure the real fanout.

## Know what p99 measures

A p99 of 400 ms means 99% of requests in the measured population finish at or below 400 ms; 1% take longer. With 10 million opens/day, that remaining 1% is still about 100,000 slow opens. Segment by endpoint, region, tenant, payload size, and result; one aggregate percentile can hide a painful subgroup. Percentiles of stages cannot simply be added to obtain end-to-end p99 because the slow requests may differ across stages.

Set a rough budget: edge and network 70 ms, API work 60 ms, database 120 ms, object retrieval 100 ms, headroom 50 ms. The pieces add to 400 ms as a planning envelope, not a guarantee. Verify with end-to-end traces under representative load, especially when concurrent requests compete for connections.

## Diagram: load, concurrency, and tail

![Average demand rises tenfold at peak, increasing concurrent requests and making the p99 tail visible.](/learning/scale-design/capacity.svg)

```aosdf-diagram
10M opens/day ÷ 86,400 ≈ 116 average RPS
Peak assumption ×10 ≈ 1,160 RPS
In-flight estimate = 1,160 RPS × 0.12 s ≈ 139
```

## Implementation: test the estimate against measured traffic

Use a load generator to replay the actual read/edit/search mix, a metrics system to collect latency buckets and saturation, and a dashboard to compare the result with the target. These are complementary roles; a dashboard does not produce load and a load test does not replace production telemetry.

| Logo | Technology and documentation | Role in this design | Check before adopting |
| :---: | --- | --- | --- |
| ![k6 logo](/learning/scale-design/logo-k6.svg) | [Grafana k6](https://grafana.com/docs/k6/latest/get-started/) | Generate a staged peak load with realistic requests. | Use seeded data and a representative endpoint mix. |
| ![prometheus logo](/learning/scale-design/logo-prometheus.svg) | [Prometheus histograms](https://prometheus.io/docs/practices/histograms/) | Collect request duration buckets, RPS, errors, and pool wait. | Choose buckets around the SLO; avoid raw document IDs as labels. |
| ![grafana logo](/learning/scale-design/logo-grafana.svg) | [Grafana](https://grafana.com/docs/grafana/latest/datasources/prometheus/query-editor/) | Plot p99, traffic, errors, and dependency saturation together. | Separate route and tenant cohorts without exploding cardinality. |

A starting k6 scenario ramps to the estimated 1,160 opens/second while mixing edits and search. Report both **offered** and **completed** RPS: a system that drops requests can appear fast if only successful responses are timed. For a classic Prometheus histogram named `http_request_duration_seconds`, a sample p99 query is:

```promql
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{route="document_open"}[5m])))
```

The metric name and `route` label are examples; instrument your actual API and bound label cardinality. Compare the p99 with connection-pool wait and database time to find the stage that causes the tail.

## Engineering exercise

Estimate average and 8× peak RPS for 2.4 million events/day. If service time is 250 ms, estimate in-flight requests. Then write one reason the estimate may be wrong and one metric that would correct it.

## Design review questions

- Why is average RPS insufficient for capacity planning?
- Can two stages each have p99 of 100 ms and guarantee end-to-end p99 of 200 ms?
- Why should a professional segment latency by tenant or endpoint?

**Review criteria:** peaks and bursts consume capacity; percentile sets do not necessarily contain the same requests; aggregates can hide a slow or overloaded cohort.

## Read further

- [Google SRE: service level objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE: monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/)
