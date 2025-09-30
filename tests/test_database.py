"""
Database model tests for LAAS Platform
Note: These tests are disabled for IAM-only mode
"""

import pytest


@pytest.mark.skip(reason="Database tests disabled for IAM-only mode")
def test_database_tests_disabled():
    """Placeholder test to indicate database tests are disabled"""
    assert True