import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import SERVICE_URLS
import logging

logger = logging.getLogger("ssp-api-gateway")


def retry_logic():
    return AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    )


async def proxy_request(method: str, service: str, path: str, headers: dict, params: dict, body: bytes):
    if service not in SERVICE_URLS or not SERVICE_URLS[service]:
        return None, 404

    target_url = f"{SERVICE_URLS[service]}/{path}"

    async with httpx.AsyncClient() as client:
        async for attempt in retry_logic():
            with attempt:
                response = await client.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    params=params,
                    content=body,
                    timeout=5.0
                )
                return response.json() if response.content else None, response.status_code
