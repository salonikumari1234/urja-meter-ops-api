import asyncio
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from src.clients.portal_client import UrjaPortalClient
from src.core.exceptions import UpstreamServiceError, UpstreamTimeoutError


def test_upstream_timeout_handling():
    async def _test():
        client = UrjaPortalClient()
        mock_http_client = AsyncMock()
        mock_http_client.is_closed = False
        mock_http_client.request.side_effect = httpx.TimeoutException("Connection timed out")
        client._client = mock_http_client
        client._is_authenticated = True

        with pytest.raises(UpstreamTimeoutError):
            await client._request_with_retry("GET", "/portal/keys")

    asyncio.run(_test())


def test_upstream_session_recovery():
    """Simulates a 401 response followed by successful re-authentication and recovery."""
    async def _test():
        client = UrjaPortalClient()

        resp_401 = httpx.Response(status_code=401)
        resp_200 = httpx.Response(status_code=200, json={"data": {"signingSecret": "secret_abc"}})

        mock_http_client = AsyncMock()
        mock_http_client.is_closed = False
        mock_http_client.request.side_effect = [resp_401, resp_200]
        client._client = mock_http_client
        client._is_authenticated = True

        async def fake_login():
            client._is_authenticated = True
            return True

        with patch.object(client, "login", side_effect=fake_login) as mock_login:
            res = await client._request_with_retry("GET", "/portal/keys")
            assert res.status_code == 200
            assert mock_login.call_count == 1

    asyncio.run(_test())
