"""Tests for storage layer (unit tests — no Docker required)."""

from __future__ import annotations

from src.storage.mongo_store import MongoStore
from src.storage.redis_bus import RedisBus


def test_mongo_store_initialises() -> None:
    """MongoStore should accept config without connecting."""
    store = MongoStore(uri="mongodb://test:27017", database="test_db")
    assert store._db_name == "test_db"


def test_redis_bus_initialises() -> None:
    """RedisBus should accept config without connecting."""
    bus = RedisBus(host="localhost", port=6379, password="test")
    assert bus._host == "localhost"
