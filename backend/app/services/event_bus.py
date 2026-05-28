import asyncio
from collections import defaultdict
from typing import Any


class TaskEventBus:
    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[tuple[str, dict[str, Any]] | None]] = defaultdict(asyncio.Queue)
        self._running: set[str] = set()

    def get_queue(self, task_id: str) -> asyncio.Queue[tuple[str, dict[str, Any]] | None]:
        return self._queues[task_id]

    def emit(self, task_id: str, event: str, data: dict[str, Any]) -> None:
        if task_id in self._queues:
            self._queues[task_id].put_nowait((event, data))

    def mark_running(self, task_id: str) -> bool:
        if task_id in self._running:
            return False
        self._running.add(task_id)
        return True

    def mark_done(self, task_id: str) -> None:
        self._running.discard(task_id)
        if task_id in self._queues:
            self._queues[task_id].put_nowait(None)


event_bus = TaskEventBus()
