from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import logging
import sys
from starlette.middleware.base import BaseHTTPResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s", "level":"%(levelname)s", "message":"%(message)s"}',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ssp-api-gateway")

# --- Rate Limiter Setup ---
# Initialize slowapi rate limiter based on client IP
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="SSP API Gateway")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Service URLs from environment variables
SERVICE_URLS = {
    "auth": os.environ.get("AUTH_SERVICE_URL"),
    "product": os.environ.get("PRODUCT_SERVICE_URL"),
    "order": os.environ.get("ORDER_SERVICE_URL"),
    "cart": os.environ.get("CART_SERVICE_URL"),
    "payment": os.environ.get("PAYMENT_SERVICE_URL"),
    "search": os.environ.get("SEARCH_SERVICE_URL"),
}

# --- Retry Logic Decorator ---
# Tenacity will retry up to 3 times, waiting 1s, then 2s, then 4s, only for specific httpx errors
def retry_logic():
    return AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout)),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying request (attempt {retry_state.attempt_number}) due to {retry_state.outcome.exception()}"
        )
    )

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("100/minute") # Global rate limit for the API Gateway
async def route_request(request: Request, service: str, path: str):
    logger.info(f"Received {request.method} request for service '{service}', path '{path}'")
    
    if service not in SERVICE_URLS or not SERVICE_URLS[service]:
        logger.error(f"Service not found or URL missing: {service}")
        raise HTTPException(status_code=404, detail="Service not found")

    service_url = f"{SERVICE_URLS[service]}/{path}"
    
    async with httpx.AsyncClient() as client:
        # Prepare the request to the downstream service
        headers = {key: value for key, value in request.headers.items() if key.lower() not in ['host']}
        body = await request.body()
        
        try:
            # Apply retry logic to the actual HTTP call
            async for attempt in retry_logic():
                with attempt:
                    response = await client.request(
                        method=request.method,
                        url=service_url,
                        headers=headers,
                        params=request.query_params,
                        content=body,
                        timeout=5.0, # Fail fast on each attempt
                    )
            
            # Return the response from the downstream service
            # Pass through the status code and content
            return JSONResponse(status_code=response.status_code, content=response.json() if response.content else None)
        
        except httpx.RequestError as e:
            logger.critical(f"Exception communicating with {service} after retries: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
