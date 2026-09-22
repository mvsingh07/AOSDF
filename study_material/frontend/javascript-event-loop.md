---
concepts: [javascript-event-loop, call-stack, event-queue]
concept_category: Frontend
difficulty: intermediate
prerequisites: []
interview_angle: >
  The classic trap question is "what does this print" with a setTimeout(fn, 0) mixed with a
  Promise — know that microtasks (Promises) always drain before the next macrotask (setTimeout).
built_at: L6-T1
diagram: true
---

# The JavaScript Event Loop

## Definition

JavaScript is single-threaded — one **call stack** executes one thing at a time. Asynchronous work
(timers, network callbacks, promises) doesn't block that stack; instead, it's queued and the **event
loop** pulls queued work back onto the stack once it's empty. There are two queues with different
priority: the **microtask queue** (Promise callbacks, `queueMicrotask`) fully drains before the event
loop moves on, while the **macrotask/callback queue** (`setTimeout`, I/O callbacks, UI events) runs one
task per loop iteration.

## Example

```javascript
console.log("1");
setTimeout(() => console.log("2"), 0);   // macrotask — queued for later
Promise.resolve().then(() => console.log("3"));  // microtask — runs before next macrotask
console.log("4");

// Output: 1, 4, 3, 2 — not 1, 2, 3, 4
```

## Diagram

```aosdf-diagram
┌──────────────┐   empty?   ┌──────────────────┐
│  Call Stack   │───────────▶│   Event Loop      │
└──────┬───────┘            └─────────┬────────┘
       │ push/pop                     │ 1. drain ALL microtasks
       ▼                              │ 2. run ONE macrotask
┌──────────────┐            ┌─────────▼────────┐   ┌───────────────────┐
│  Executing    │◀───────────│  Microtask Queue │   │ Macrotask Queue    │
│  synchronous  │            │  (Promises)       │   │ (setTimeout, I/O)  │
│  code          │            └──────────────────┘   └───────────────────┘
```

## Why This Trips People Up

`async`/`await` is syntax sugar over Promises — an `await` inside an `async` function suspends that
function and schedules its continuation as a microtask, it does not spawn a new thread. Understanding
this is the difference between correctly reasoning about ordering bugs in real code and guessing.
