import httpx
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from httpx import AsyncClient

from logger import logger
from router_v1 import Router

app = FastAPI(title="Easy Getaway")

router = Router()

# tests
# Замени или добавь:
router.add_route("/headers/*", "https://httpbin.org")
router.add_route("/headers", "https://httpbin.org")


@app.api_route("/{catch_path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, catch_path: str):
    logger.info(f"Запрос: {request.method} {request.url.path}")

    target, remaining, route_type = router.find_target(f"/{catch_path}")
    logger.info(f"Маршрут найден: {target} остаток: {remaining}")

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

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="[!] Backend connection error [!]")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="[!] Backend timeout error [!]")
