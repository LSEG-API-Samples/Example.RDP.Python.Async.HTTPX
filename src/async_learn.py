import asyncio
import time


async def task_function(name, duration, fail=False):
    print(f"  Task {name}: Starting (will sleep for {duration}s)")
    await asyncio.sleep(duration)
    if fail:
        raise ValueError(f"Task {name} failed!")
    print(f"  Task {name}: Finished")
    return f"Result of {name}"


# ─────────────────────────────────────────────
# asyncio.gather
# ─────────────────────────────────────────────
# • Available since Python 3.4
# • Accepts coroutines or Tasks
# • Returns a list of results in the same order as inputs
# • Error behaviour (default): if one task raises, the exception is
#   propagated immediately to the caller, but the OTHER tasks keep
#   running in the background (they are NOT cancelled).
# • return_exceptions=True: exceptions are returned as result values
#   instead of being raised, so all tasks always run to completion.
# • Good for fire-and-forget fan-out or when you need return_exceptions.

async def demo_gather():
    print("\n=== asyncio.gather (no failures) ===")
    start = time.perf_counter()
    results = await asyncio.gather(
        task_function("A", 3),
        task_function("B", 1),
        task_function("C", 2),
    )
    print(f"  Done in {time.perf_counter() - start:.2f}s | Results: {results}")

    print("\n=== asyncio.gather with return_exceptions=True ===")
    start = time.perf_counter()
    results = await asyncio.gather(
        task_function("A", 1),
        task_function("B", 0.5, fail=True),   # will raise
        task_function("C", 1),
        return_exceptions=True,                # exceptions become values
    )
    print(f"  Done in {time.perf_counter() - start:.2f}s | Results: {results}")


# ─────────────────────────────────────────────
# asyncio.TaskGroup  (Python 3.11+)
# ─────────────────────────────────────────────
# • Context-manager-based structured concurrency.
# • Tasks are created with tg.create_task() inside the `async with` block.
# • When the block exits all tasks are AWAITED automatically.
# • Error behaviour: if ANY task raises, ALL remaining tasks are
#   cancelled immediately, then the exception is re-raised.
#   Multiple simultaneous exceptions are collected into an ExceptionGroup.
# • Cleaner resource management; preferred for structured concurrency.

async def demo_task_group():
    print("\n=== asyncio.TaskGroup (no failures) ===")
    start = time.perf_counter()
    results = []
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(task_function("A", 3))
        t2 = tg.create_task(task_function("B", 1))
        t3 = tg.create_task(task_function("C", 2))
    # All tasks are guaranteed finished here
    results = [t1.result(), t2.result(), t3.result()]
    print(f"  Done in {time.perf_counter() - start:.2f}s | Results: {results}")

    print("\n=== asyncio.TaskGroup with a failing task ===")
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(task_function("A", 1))
            tg.create_task(task_function("B", 0.1, fail=True))  # raises quickly
            tg.create_task(task_function("C", 1))               # will be cancelled
    except* ValueError as eg:
        print(f"  Caught ExceptionGroup errors: {eg}")


# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
# | Feature                  | gather                  | TaskGroup (3.11+)       |
# |--------------------------|-------------------------|-------------------------|
# | API style                | function call           | async context manager   |
# | Task creation            | pass coroutines/tasks   | tg.create_task()        |
# | On first exception       | others keep running *   | others are cancelled    |
# | Multiple exceptions      | only first propagated   | ExceptionGroup          |
# | return_exceptions        | yes                     | no (use try/except)     |
# | Structured concurrency   | no                      | yes                     |
# | Python version           | 3.4+                    | 3.11+                   |
#
# * Unless return_exceptions=False (default) and you shield tasks.

async def main():
    await demo_gather()
    await demo_task_group()


if __name__ == "__main__":
    asyncio.run(main())


