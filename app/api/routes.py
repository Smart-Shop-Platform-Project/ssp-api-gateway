from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.services.gateway import proxy_request
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("100/minute")
async def route_request(request: Request, service: str, path: str):
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
    body = await request.body()

    content, status_code = await proxy_request(
        request.method, service, path, headers, request.query_params, body
    )

    if status_code == 404:
        raise HTTPException(status_code=404, detail="Service not found")

    return JSONResponse(status_code=status_code, content=content)
