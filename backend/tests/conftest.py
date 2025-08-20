"""
Pytest configuration and fixtures.
Similar to test setup in .NET with dependency injection for tests.
"""

import pytest
from pathlib import Path

from fastapi.testclient import TestClient
from app.core.config import get_settings


@pytest.fixture
def temp_upload_dir(tmp_path: Path):
    """Temporary directory for uploads (auto-cleaned by pytest)."""
    return str(tmp_path)


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing (bytes)."""
    return b"""date,region,product,sales,units
2024-01-01,North,Widget A,100.50,10
2024-01-02,South,Widget B,200.75,15
2024-01-03,East,Widget A,150.25,12
2024-01-04,West,Widget C,300.00,20
2024-01-05,North,Widget B,175.50,14"""


@pytest.fixture(autouse=True)
def mock_settings(temp_upload_dir, monkeypatch):
    """
    Patch get_settings used across the app so tests use a temporary upload dir
    and a blank OpenAI key (tests should patch specifics where needed).
    This runs before other fixtures/tests so importing app inside client() sees patched settings.
    """
    try:
        settings = get_settings()
    except Exception:
        # If get_settings fails, create a minimal object with attribute assignment support.
        class _S: pass
        settings = _S()
    # Ensure attributes exist and set test values
    setattr(settings, "upload_dir", temp_upload_dir)
    setattr(settings, "openai_api_key", "")
    # Monkeypatch the function so any later import of get_settings() returns this instance
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings, raising=False)
    # also set env vars commonly read
    monkeypatch.setenv("UPLOAD_DIR", str(temp_upload_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "")
    yield


@pytest.fixture
def client():
    """Import app after mock_settings has run so app picks up patched settings."""
    from app.main import app
    return TestClient(app)