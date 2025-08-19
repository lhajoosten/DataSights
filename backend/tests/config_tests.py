"""
Pytest configuration and fixtures.
Similar to test setup in .NET with dependency injection for tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings


@pytest.fixture
def client():
    """Test client fixture for API testing."""
    return TestClient(app)


@pytest.fixture
def temp_upload_dir():
    """Temporary upload directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return b"""date,region,product,sales,units
2024-01-01,North,Widget A,100.50,10
2024-01-02,South,Widget B,200.75,15
2024-01-03,East,Widget A,150.25,12
2024-01-04,West,Widget C,300.00,20
2024-01-05,North,Widget B,175.50,14"""


@pytest.fixture
def mock_settings(temp_upload_dir):
    """Mock settings for testing."""
    def _get_test_settings():
        settings = get_settings()
        settings.upload_dir = temp_upload_dir
        settings.openai_api_key = ""  # Use fallback mode
        return settings
    
    return _get_test_settings