"""
API integration tests following .NET Web API testing patterns.
Using TestClient for end-to-end API testing.
"""

import io
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

def _find_upload_path(app):
    # try to find a route that looks like CSV upload
    for r in app.routes:
        p = getattr(r, "path", "")
        if "upload" in p and "csv" in p:
            return p
    # fallback to common variants
    candidates = ["/api/csv/upload", "/api/v1/csv/upload", "/csv/upload", "/upload"]
    for c in candidates:
        for r in app.routes:
            if getattr(r, "path", "") == c:
                return c
    # if nothing found, raise with route listing for debugging
    available = "\n".join(f"{getattr(r,'name',r)} -> {getattr(r,'path', '')}" for r in app.routes)
    raise RuntimeError(f"Could not find CSV upload route. Available routes:\n{available}")


def _find_chat_path(app):
    # try to find a route that looks like chat ask
    for r in app.routes:
        p = getattr(r, "path", "")
        if "chat" in p and "ask" in p:
            return p
    # fallback to common variants
    candidates = ["/api/chat/ask", "/api/v1/chat/ask", "/chat/ask", "/ask"]
    for c in candidates:
        for r in app.routes:
            if getattr(r, "path", "") == c:
                return c
    available = "\n".join(f"{getattr(r,'name',r)} -> {getattr(r,'path', '')}" for r in app.routes)
    raise RuntimeError(f"Could not find chat ask route. Available routes:\n{available}")

class TestChatAPI:
    """Integration tests for chat endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def uploaded_file_id(self, client, sample_csv_content):
        """Upload a file and return its ID for testing."""
        files = {"file": ("test.csv", io.BytesIO(sample_csv_content), "text/csv")}
        upload_path = _find_upload_path(client.app)
        response = client.post(upload_path, files=files)

        # accept 200 OK or 201 Created
        if response.status_code not in (200, 201):
            print("DEBUG: CSV upload failed:", response.status_code)
            try:
                print("DEBUG: response.json():", response.json())
            except Exception:
                print("DEBUG: response.text():", response.text)
            pytest.fail(f"CSV upload expected 200/201 but got {response.status_code}")

        # Prefer JSON payload but fall back to Location header if present
        data = None
        try:
            data = response.json()
        except Exception:
            data = None

        if data:
            return data.get("file_id") or data.get("id") or data.get("fileId")
        # try Location header (e.g. /api/csv/files/{id})
        loc = response.headers.get("Location") or response.headers.get("location")
        if loc:
            return loc.rstrip("/").split("/")[-1]

        pytest.fail("Upload response did not include file id in body or Location header")

    def test_chat_request_success(self, client, uploaded_file_id):
        request_data = {
            "file_id": uploaded_file_id,
            "question": "Show sales data",
            "context": []
        }
        chat_path = _find_chat_path(client.app)
        response = client.post(chat_path, json=request_data)
        assert response.status_code == 200
        resp = response.json()
        assert "message" in resp
        msg = resp["message"]
        assert isinstance(msg, dict)
        assert msg.get("content") or resp.get("chart_data") is not None or resp.get("requires_clarification") is not None

    def test_chat_request_file_not_found(self, client):
        """Test file not found scenario - error handling."""
        # Arrange
        request_data = {
            "file_id": "nonexistent_file",
            "question": "Show sales data",
            "context": []
        }

        # Act
        chat_path = _find_chat_path(client.app)
        response = client.post(chat_path, json=request_data)

        # Assert expected not-found status
        assert response.status_code == 404

        # tolerate different error formats: JSON body or plain string - assert the response mentions file/not found
        try:
            error_data = response.json()
        except Exception:
            error_text = response.text or ""
            assert "not found" in error_text.lower() or "file" in error_text.lower()
            return

        # check the whole JSON payload as string for expected words
        full = json.dumps(error_data)
        assert "file" in full.lower() or "not found" in full.lower()