from typing import Optional, Tuple
from fastapi import FastAPI, Request, Response as FastAPIResponse
from httpx import AsyncClient, Response as HTTPXResponse
from fastapi.exceptions import HTTPException
import httpx

from middleware.base import Middleware
from middleware.logging_middleware import LoggingMiddleware
from router_v1 import Router

app = FastAPI(title="Easy Getaway")
router = Router()

middlewares: list[Middleware] = []
middlewares.append(LoggingMiddleware())

router.add_route("/headers", "https://httpbin.org/")


# funcs for router
async def proccess_middleware(request: Request, httpx_response: Optional[HTTPXResponse] = None) -> Tuple[Request, Optional[FastAPIResponse]]:
    for middleware in middlewares:
        result = await middleware.before_request(request)
        if isinstance(result, FastAPIResponse):
            return request, result
        request = result
    
    if httpx_response is None:
        return request, None

    fastapi_response = FastAPIResponse(
        content=httpx_response.content,
        status_code=httpx_response.status_code,
        headers=dict(httpx_response.headers)
    )

    for middleware in reversed(middlewares):
        fastapi_response = await middleware.after_response(request, fastapi_response)

    return request, fastapi_response


@app.api_route("/{catch_path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, catch_path: str):
    request, middleware_response = await proccess_middleware(request)
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

        request, proccessed_response = await proccess_middleware(request, httpx_response)

        return proccessed_response

    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="[!] Backend connection error [!]")
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="[!] Backend timeout error [!]")
