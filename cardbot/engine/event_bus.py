from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


EventCallback = Callable[..., Any]


@dataclass
class _ListenerEntry:
    """Internal listener record used for deterministic dispatch ordering."""

    priority: int
    order: int
    callback: EventCallback


class EventBus:
    """Deterministic event bus for engine trigger dispatch.

    Listeners are ordered by:
    1) higher priority first
    2) registration order as tie-breaker
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[_ListenerEntry]] = {}
        self._counter: int = 0

    def register(self, event: str, callback: EventCallback, priority: int = 0) -> None:
        """Register a callback for an event name."""
        bucket = self._listeners.setdefault(event, [])
        bucket.append(_ListenerEntry(priority=priority, order=self._counter, callback=callback))
        self._counter += 1
        bucket.sort(key=lambda entry: (-entry.priority, entry.order))

    def unregister(self, event: str, callback: EventCallback) -> None:
        """Unregister a callback for an event name if present."""
        bucket = self._listeners.get(event)
        if not bucket:
            return
        self._listeners[event] = [entry for entry in bucket if entry.callback is not callback]

    def dispatch(self, event: str, **kwargs: Any) -> None:
        """Dispatch an event to listeners in deterministic order."""
        listeners = tuple(self._listeners.get(event, ()))
        for entry in listeners:
            entry.callback(event=event, **kwargs)


# TODO: add event tracing hooks for offline replay debugging.
