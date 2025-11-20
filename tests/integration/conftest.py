# tests/integration/conftest.py
import pytest
from django.db import connection


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers",
        "postgresql_only: mark test to run only on PostgreSQL database (skipped on SQLite/MySQL)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked as postgresql_only when not using PostgreSQL"""
    for item in items:
        if "postgresql_only" in item.keywords and connection.vendor != "postgresql":
            item.add_marker(
                pytest.mark.skip(
                    reason="Test requires PostgreSQL (concurrency not supported on SQLite/MySQL)"
                )
            )
