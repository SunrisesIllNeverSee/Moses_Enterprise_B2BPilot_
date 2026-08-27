"""Repository — loads demo data from disk into domain objects.

The repository layer is the shared data-access point for CLI/TUI/MCP.
No interface layer reads data files directly; all go through the repository
(per `21`: "Do not let CLI/TUI/MCP each implement business logic independently").
"""
from __future__ import annotations

from .demo_repository import DemoRepository
from .sqlite_repository import SQLiteRepository

__all__ = ["DemoRepository", "SQLiteRepository"]
