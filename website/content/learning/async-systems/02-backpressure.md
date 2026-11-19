# Capacity, backpressure, and scheduling

A queue absorbs a temporary mismatch between incoming work and worker capacity. It does not create capacity. If jobs arrive faster than they finish for long enough, the oldest job gets older until the promised completion time is missed.

## Calculate the backlog before scaling

Suppose export requests arrive at **120 jobs/minute** during a 20-minute peak. Six workers each complete **15 jobs/minute**, so service capacity is **90/minute**. Backlog grows at **30/minute**, reaching about **600 jobs** after 20 minutes. Once arrivals return to **60/minute**, spare capacity is **30/minute** and draining those 600 jobs takes another **20 minutes**. A 20-minute burst can therefore affect users for roughly 40 minutes.

These are simple averages. Real service times vary, large exports may dominate, and a shared file store can become slower as concurrency rises. Measure the oldest job age and completion latency, not only queue depth.

## Choose an overload policy

Before increasing consumers, decide what the system should do at capacity:

| Policy | When it helps | Cost |
| --- | --- | --- |
| Add workers | Downstream storage and quota have spare capacity | More concurrent load and cost |
| Limit intake | Work can be refused or deferred honestly | Some requests get `429` or a clear busy response |
| Prioritize | Some jobs have stronger deadlines | Low-priority starvation needs a limit |
| Coalesce | Repeated requests ask for the same output | Requires a stable key and freshness rule |
| Shed optional work | Secondary work is not required for completion | Product must accept reduced functionality |

Set a maximum in-flight count per worker and a per-tenant quota. A broker prefetch or batch setting that hands one worker hundreds of slow jobs can hide backlog from other workers. Schedule `cron` jobs through the same capacity model: a nightly run that enqueues 10,000 exports is still an arrival burst.

## Diagram: the backlog as a buffer

![At 120 arrivals per minute and 90 completed jobs per minute, the queue grows by 30 jobs per minute.](/learning/async-systems/backpressure.svg)

```aosdf-diagram
Arrivals (120/min) ──▶ Queue (+30/min) ──▶ Workers (90/min) ──▶ File store
                          │                    │
                          └── oldest age       └── concurrency cap
                              reveals delay        protects dependency
```

[Explore the full queue delivery diagram](/queue-delivery-lifecycle.archify.html) to see where the worker claim sits in the delivery path.

## Use the right trigger

Scale on a signal close to user impact, such as oldest job age relative to a completion target, while considering queue depth and worker utilization. Queue depth alone has no universal “bad” value: 600 one-second jobs and 600 ten-minute jobs are different. If the dependency is the bottleneck, more workers amplify failure. Apply backpressure at intake or worker concurrency instead.

## Try it

Recalculate the example for four workers and for eight workers. Assume the file store handles at most 100 jobs/minute. Decide which worker count you would allow, what admission rule you would use during a peak, and which metric would page a human.

## Check your understanding

- Why can a growing queue be healthy briefly but harmful over time?
- Why might adding workers make throughput worse?
- What does oldest job age show that queue depth does not?

**Answer guide:** bursts can be buffered if they drain before deadlines; a saturated dependency can slow under more concurrency; age measures the delay experienced by work already accepted.

## Read further

- [Amazon SQS CloudWatch metrics](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-available-cloudwatch-metrics.html)
- [RabbitMQ consumer prefetch](https://www.rabbitmq.com/docs/consumer-prefetch)
