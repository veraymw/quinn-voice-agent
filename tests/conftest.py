"""
Pytest configuration and fixtures for Quinn Voice Agent tests
"""
import pytest
import asyncio
import httpx
from typing import AsyncGenerator
from datetime import datetime

# Test configuration
TEST_SERVER_URL = "http://localhost:8000"
TEST_PHONE_NUMBER = "+19296027097"  # Default test phone number


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for API testing"""
    async with httpx.AsyncClient(timeout=30) as client:
        yield client


@pytest.fixture
def test_sms_payload():
    """Standard SMS test payload"""
    return {
        "call_control_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "phone_number": TEST_PHONE_NUMBER,
        "first_name": "Test",
        "last_name": "User",
        "company": "Test Company",
        "region": "Americas",
        "qualification_level": "SQL",
        "qualification_score": 85
    }


@pytest.fixture
def server_health_check(http_client: httpx.AsyncClient):
    """Check if the server is running before tests"""
    async def _check():
        try:
            response = await http_client.get(f"{TEST_SERVER_URL}/")
            return response.status_code == 200
        except httpx.ConnectError:
            return False
    return _check


class TestConfig:
    """Test configuration constants"""
    SERVER_URL = TEST_SERVER_URL
    DEFAULT_PHONE = TEST_PHONE_NUMBER
    TIMEOUT = 30
