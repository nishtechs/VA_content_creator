"""
LLM execution helper with rate-limit handling.
Wraps CrewAI crew.kickoff() with exponential backoff + jitter on RateLimitError.

A FRESH agent is built per attempt (via the provided factory) so that a stateful
executor left "running" by a previous failure/retry never gets reused — this avoids
the "Executor is already running" RuntimeError.
"""

import time
import random
import logging
from typing import Callable

from crewai import Agent, Crew, Process, Task

logger = logging.getLogger("va_creator.llm_runner")

# Detect rate-limit / transient errors by class name or message text
_RATE_LIMIT_MARKERS = (
    "ratelimiterror",
    "rate limit",
    "429",
    "too many requests",
    "overloaded",
    "service unavailable",
    "timeout",
    "executor is already running",  # stale executor — fresh agent fixes it
)


def _is_retryable(exc: Exception) -> bool:
    """Return True if the exception looks like a transient / rate-limit error."""
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    return any(marker in name or marker in msg for marker in _RATE_LIMIT_MARKERS)


def run_crew_with_retry(
    agent_factory: Callable[[], Agent],
    task_factory: Callable[[Agent], Task],
    max_retries: int = 6,
    base_delay: float = 8.0,
):
    """
    Run a single-agent, single-task crew with retry + exponential backoff.

    A new agent and task are constructed on EACH attempt to guarantee clean state.

    Args:
        agent_factory: callable that returns a fresh Agent
        task_factory: callable that takes the fresh Agent and returns a Task
        max_retries: max number of attempts on transient errors
        base_delay: initial backoff delay in seconds

    Returns:
        tuple (result, task) — the crew kickoff result and the task
        (so callers can read task.output.raw).

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        agent = agent_factory()
        task = task_factory(agent)
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )
        try:
            result = crew.kickoff()
            return result, task
        except Exception as e:  # noqa: BLE001 — we inspect and re-raise below
            last_exc = e
            if not _is_retryable(e) or attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 2), 60.0)
            logger.warning(
                f"LLM call failed (attempt {attempt + 1}/{max_retries}): "
                f"{type(e).__name__}. Retrying in {delay:.1f}s..."
            )
            time.sleep(delay)

    if last_exc:
        raise last_exc
