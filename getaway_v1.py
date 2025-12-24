import httpx
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from httpx import AsyncClient
from middleware.base import Middleware
from middleware.logging_middleware import LoggingMiddleware
from router_v1 import Router

app = FastAPI(title="Easy Getaway")
router = Router()

middlewares: list[Middleware] = []
middlewares.append(LoggingMiddleware())

router.add_route("/headers", "https://httpbin.org/")

# funcs for router
async def proccess_middleware(request: Request, response: Response = None):
    for middleware in middlewares:
        request = await middleware.before_request(request)

    if response:
        for middleware in reversed(middlewares):
            response = await middleware.after_response(request, response)

    return request, response


@app.api_route("/{catch_path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, catch_path: str):
    request, _ = await proccess_middleware(request)

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
            response = await client.request(
                method=request.method, url=url, headers=r_headers, content=body
            )
            
        _, response = await proccess_middleware(request, response)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="[!] Backend connection error [!]")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="[!] Backend timeout error [!]")
