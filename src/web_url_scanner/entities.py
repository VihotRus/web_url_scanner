"""Entities module."""

import time
from dataclasses import dataclass, field


@dataclass
class WriteURL:
    url: str
    depth: int
    read_timestamp: float = field(default_factory=lambda: time.time())

    def __str__(self):
        return f"URL {self.url} depth {self.depth} read timestamp {self.read_timestamp}"

@dataclass
class WriteBrokenURL:
    url: str
    read_timestamp: float = field(default_factory=lambda: time.time())

    def __str__(self):
        return f"URL {self.url} read timestamp {self.read_timestamp}"
