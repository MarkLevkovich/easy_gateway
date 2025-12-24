from typing import Any, Optional, Required, Tuple

import httpx
from fastapi import FastAPI, Request
from fastapi import Response as FastAPIResponse
from fastapi.exceptions import HTTPException
from httpx import AsyncClient
from httpx import Response as HTTPXResponse

from middleware.base import Middleware
from middleware.logging_middleware import LoggingMiddleware
from middleware.rate_limit_middleware import RateLimitMiddleware
from router_v1 import Router

app = FastAPI(title="Easy Getaway")
router = Router()

middlewares: list[Middleware] = []
middlewares.append(RateLimitMiddleware(requests_per_minute=5))
middlewares.append(LoggingMiddleware())


router.add_route("/headers", "https://httpbin.org/")


async def process_request_middleware(
    request: Request,
) -> Tuple[Request, Optional[FastAPIResponse]]:
    for middleware in middlewares:
        result = await middleware.before_request(request)
        if isinstance(result, FastAPIResponse):
            return request, result
        request = result
    return request, None


async def process_response_middleware(
    request: Request, httpx_response: HTTPXResponse
) -> FastAPIResponse:
    fastapi_response = FastAPIResponse(
        content=httpx_response.content,
        status_code=httpx_response.status_code,
        headers=dict(httpx_response.headers),
    )

    for middleware in reversed(middlewares):
        fastapi_response = await middleware.after_response(request, fastapi_response)

    return fastapi_response


@app.api_route("/{catch_path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, catch_path: str):
    print(f"🎯 HANDLER CALLED: {request.method} {catch_path}")
    request, middleware_response = await process_request_middleware(request)
    if middleware_response is not None:
        return middleware_response

    target, remaining, route_type = router.find_target(f"/{catch_path}")

    if not target:
        raise HTTPException(404)

    if route_type == "exact":
        url = target

    else:
        if remaining:
            url = target + (remaining if remaining.startswith("/") else f"/{remaining}")
        else:
            url = target + "/"

    body = await request.body()
    r_headers = dict(request.headers)
    r_headers.pop("Host", None)

    if "accept" not in r_headers:
        r_headers["Accept"] = "application/json"

    try:
        async with AsyncClient(timeout=30.0) as client:
            httpx_response: HTTPXResponse = await client.request(
                method=request.method, url=url, headers=r_headers, content=body
            )

        proccessed_response = await process_response_middleware(request, httpx_response)

        return proccessed_response

    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="[!] Backend connection error [!]")

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="[!] Backend timeout error [!]")
