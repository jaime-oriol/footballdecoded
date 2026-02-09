"""Database module for FootballDecoded.

Exposes DatabaseManager (from connection.py) as the single entry point
for all DB operations: pool management, inserts, queries, and schema setup.
"""

__all__ = [
    "DatabaseManager",
]
