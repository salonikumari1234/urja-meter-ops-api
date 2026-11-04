import asyncio
import time
from typing import Any, Dict, List, Optional
import httpx
from src.config.settings import settings
from src.core.exceptions import UpstreamServiceError, UpstreamTimeoutError
from src.core.logging import logger
from src.utils.hmac_utils import generate_export_signature


class UrjaPortalClient:
    """
    Client for interacting with the upstream Urja Meter Ops SvelteKit portal.
    Handles Better-Auth session tokens, automated re-login, CSRF protections,
    and HMAC-SHA256 signed exports.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = (base_url or settings.upstream_portal_url).rstrip("/")
        self.username = username or settings.upstream_username
        self.password = password or settings.upstream_password
        self.timeout = timeout or settings.upstream_timeout_seconds

        self._client: Optional[httpx.AsyncClient] = None
        self._auth_lock = asyncio.Lock()
        self._is_authenticated = False
        self._session_token: Optional[str] = None
        self._signing_secret: Optional[str] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Initializes or returns the cached async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=False,
                verify=True
            )
        return self._client

    async def close(self) -> None:
        """Closes the underlying HTTP client session."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            self._is_authenticated = False

    async def login(self) -> bool:
        """
        Authenticates against the upstream SvelteKit form action endpoint.
        Stores session cookies for subsequent requests.
        """
        async with self._auth_lock:
            client = await self.get_client()
            login_url = f"{self.base_url}/login"

            headers = {
                "Accept": "application/json",
                "x-sveltekit-action": "true",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self.base_url,
                "Referer": login_url,
                "User-Agent": "Urja-Meter-Ops-API/1.0"
            }
            body = {
                "email": self.username,
                "password": self.password
            }

            try:
                logger.info(f"Initiating authentication against upstream portal: {self.base_url}")
                response = await client.post(login_url, data=body, headers=headers)

                # Upstream returns 200 with JSON redirect descriptor on success
                if response.status_code == 200:
                    token = client.cookies.get("__Secure-better-auth.session_token")
                    if token:
                        self._session_token = token
                    self._is_authenticated = True
                    logger.info("Successfully authenticated against upstream portal.")
                    return True
                else:
                    logger.error(
                        f"Upstream authentication failed with HTTP {response.status_code}: {response.text[:200]}"
                    )
                    raise UpstreamServiceError(
                        f"Upstream authentication rejected with status {response.status_code}."
                    )
            except httpx.TimeoutException as exc:
                logger.error(f"Timeout during upstream authentication: {exc}")
                raise UpstreamTimeoutError("Timeout during upstream authentication.")
            except httpx.RequestError as exc:
                logger.error(f"Network error during upstream authentication: {exc}")
                raise UpstreamServiceError(f"Network error connecting to upstream portal: {exc}")

    async def _ensure_authenticated(self) -> None:
        """Ensures that the client has an active authenticated session."""
        if not self._is_authenticated:
            await self.login()

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> httpx.Response:
        """
        Executes an HTTP request with automatic session expiration recovery
        and bounded transient retry logic.
        """
        await self._ensure_authenticated()
        client = await self.get_client()
        url = f"{self.base_url}{path}"

        req_headers = {
            "User-Agent": "Urja-Meter-Ops-API/1.0",
            "Referer": f"{self.base_url}/meters"
        }
        if headers:
            req_headers.update(headers)

        try:
            response = await client.request(method, url, params=params, headers=req_headers)

            # Check for session expiration (302/303 redirect to /login or 401)
            is_redirect_to_login = (
                response.status_code in (302, 303)
                and "/login" in response.headers.get("location", "")
            )
            if response.status_code == 401 or is_redirect_to_login:
                if retry_count < settings.upstream_max_retries:
                    logger.warning("Upstream session expired. Re-authenticating and retrying...")
                    self._is_authenticated = False
                    await self.login()
                    return await self._request_with_retry(
                        method, path, params, headers, retry_count + 1
                    )
                else:
                    raise UpstreamServiceError("Session expired and maximum re-auth retries exceeded.")

            return response
        except httpx.TimeoutException as exc:
            logger.error(f"Upstream timeout requesting {path}: {exc}")
            raise UpstreamTimeoutError(f"Upstream timeout requesting {path}.")
        except httpx.RequestError as exc:
            if retry_count < settings.upstream_max_retries:
                backoff = settings.upstream_retry_backoff_factor * (2 ** retry_count)
                logger.warning(f"Upstream request failed ({exc}). Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                return await self._request_with_retry(
                    method, path, params, headers, retry_count + 1
                )
            raise UpstreamServiceError(f"Failed requesting upstream {path}: {exc}")

    async def get_signing_secret(self) -> str:
        """Retrieves HMAC signing secret from /portal/keys."""
        if self._signing_secret:
            return self._signing_secret

        res = await self._request_with_retry("GET", "/portal/keys")
        if res.status_code != 200:
            raise UpstreamServiceError(f"Failed to fetch keys: HTTP {res.status_code}")

        data = res.json().get("data", {})
        secret = data.get("signingSecret")
        if not secret:
            raise UpstreamServiceError("Upstream returned empty signing secret.")

        self._signing_secret = secret
        return secret

    async def fetch_all_meters_export(self) -> List[Dict[str, Any]]:
        """
        Executes signed bulk export to retrieve the complete inventory of all meters.
        """
        secret = await self.get_signing_secret()
        timestamp = str(int(time.time()))
        query = "page=1"
        signature = generate_export_signature("GET", "/portal/export", query, timestamp, secret)

        headers = {
            "x-timestamp": timestamp,
            "x-signature": signature
        }

        res = await self._request_with_retry("GET", f"/portal/export?{query}", headers=headers)
        if res.status_code != 200:
            raise UpstreamServiceError(f"Failed export request: HTTP {res.status_code}")

        payload = res.json()
        meters = payload.get("data", [])
        logger.info(f"Retrieved {len(meters)} meters from upstream bulk export.")
        return meters

    async def fetch_all_transformers(self) -> List[Dict[str, Any]]:
        """
        Paginates through /portal/dts to retrieve all distribution transformers.
        """
        all_dts: List[Dict[str, Any]] = []
        page = 1

        while True:
            res = await self._request_with_retry("GET", "/portal/dts", params={"page": page})
            if res.status_code != 200:
                raise UpstreamServiceError(f"Failed to fetch DTs page {page}: HTTP {res.status_code}")

            data = res.json()
            items = data.get("data", [])
            total = data.get("total", 0)

            if not items:
                break

            all_dts.extend(items)
            if len(all_dts) >= total:
                break
            page += 1

        logger.info(f"Retrieved {len(all_dts)} transformers across {page} pages.")
        return all_dts

    async def fetch_meter_energy(self, meter_id: str) -> List[Dict[str, Any]]:
        """
        Fetches consumption / energy readings for a specific meter.
        """
        res = await self._request_with_retry("GET", f"/portal/meters/{meter_id}/energy")
        if res.status_code == 404:
            return []
        if res.status_code != 200:
            raise UpstreamServiceError(
                f"Failed fetching energy for meter {meter_id}: HTTP {res.status_code}"
            )
        return res.json().get("data", [])

    async def fetch_meter_geo(self, meter_id: str) -> Optional[Dict[str, float]]:
        """
        Fetches latitude and longitude coordinates for a meter.
        """
        res = await self._request_with_retry("GET", f"/portal/meters/{meter_id}/geo")
        if res.status_code == 404:
            return None
        if res.status_code != 200:
            raise UpstreamServiceError(
                f"Failed fetching geo for meter {meter_id}: HTTP {res.status_code}"
            )
        data = res.json().get("data", {})
        try:
            return {
                "latitude": float(data["latitude"]),
                "longitude": float(data["longitude"])
            }
        except (KeyError, ValueError, TypeError):
            return None
