---
concepts: [concurrency, parallelism, thread-vs-process, async-await]
concept_category: Concurrency
difficulty: advanced
prerequisites: [javascript-event-loop]
interview_angle: >
  Know the precise distinction between concurrency and parallelism (one CPU core interleaving tasks
  vs. genuinely simultaneous execution on multiple cores) — this is asked constantly and conflated
  constantly.
built_at: L6-T1
diagram: true
---

# Concurrency Models

## Definition

- **Concurrency:** structuring a program to handle multiple tasks that are in progress at overlapping
  times — doesn't require multiple CPU cores; a single core can interleave tasks (this is exactly what
  the JS event loop does with async operations, see
  `study_material/frontend/javascript-event-loop.md`).
- **Parallelism:** actually executing multiple tasks at the exact same instant, requiring multiple CPU
  cores. Concurrency is about *structure*; parallelism is about *simultaneous execution* — a
  single-threaded event loop is concurrent but never parallel.
- **Process vs. thread:** a process has its own isolated memory space (crash-safe from other processes,
  but expensive to create and communicate across); a thread shares memory with other threads in the same
  process (cheap to create, fast to communicate, but a bug in one thread can corrupt shared state used by
  another).
- **`async`/`await`:** a way to write asynchronous, non-blocking code that *reads* like synchronous code
  — the runtime suspends the function at each `await` and resumes it later, without blocking the
  underlying thread while waiting.

## Example

```python
# Concurrency without parallelism — one thread, overlapping I/O waits
async def fetch_all(urls):
    return await asyncio.gather(*(fetch(url) for url in urls))
    # while one request is waiting on the network, another can proceed —
    # but only one line of Python bytecode ever executes at a time (GIL)

# True parallelism — separate processes, separate CPU cores
with multiprocessing.Pool(4) as pool:
    results = pool.map(cpu_heavy_function, data_chunks)
```

## Diagram

```aosdf-diagram
Concurrency (1 core, interleaved):    Parallelism (multiple cores, simultaneous):
Core: [A][B][A][B][A][B]              Core 1: [A][A][A][A]
      (never actually simultaneous)   Core 2: [B][B][B][B]
```

## The Practical Takeaway

I/O-bound work (waiting on network/disk) benefits from concurrency alone — `async`/`await` or an event
loop is enough, no extra cores needed. CPU-bound work (heavy computation) needs actual parallelism —
multiple processes or threads on multiple cores — since concurrency alone can't speed up work that's
never waiting on anything.
