from typing import Any, Dict, Optional, Required, Tuple

import httpx
from fastapi import FastAPI, Request
from fastapi import Response as FastAPIResponse
from fastapi.exceptions import HTTPException
from httpx import AsyncClient
from httpx import Response as HTTPXResponse

from gateway.handler import process_request_middleware, process_response_middleware
from middleware.base import Middleware
from middleware.logging_middleware import LoggingMiddleware
from middleware.rate_limit_middleware import RateLimitMiddleware
from router_v1 import Router


class EasyGateway:
    def __init__(self, config: Dict[str, Any] = None):
        # init basics apps
        self.app = FastAPI(title="Easy Gateway")
        self.router = Router()
        self.middlewares: list[Middleware] = []
        self._setup_middleware()
        self._setup_routes()
        self._setup_handler()

    def _setup_middleware(self):
        # later from yaml
        self.middlewares.append(RateLimitMiddleware(requests_per_minute=5))
        self.middlewares.append(LoggingMiddleware())

    def _setup_routes(self):
        # later from yaml
        self.router.add_route("/headers", "https://httpbin.org/")

    def _setup_handler(self):
        @self.app.api_route("/{catch_path:path}", methods=["GET", "POST"])
        async def catch_all(request: Request, catch_path: str):
            print(f"🎯 HANDLER CALLED: {request.method} {catch_path}")
            request, middleware_response = await process_request_middleware(
                self.middlewares, request
            )
            if middleware_response is not None:
                return middleware_response

            target, remaining, route_type = self.router.find_target(f"/{catch_path}")

            if not target:
                raise HTTPException(404)

            if route_type == "exact":
                url = target

            else:
                if remaining:
                    url = target + (
                        remaining if remaining.startswith("/") else f"/{remaining}"
                    )
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

                proccessed_response = await process_response_middleware(
                    self.middlewares, request, httpx_response
                )

                return proccessed_response

            except httpx.ConnectError:
                raise HTTPException(
                    status_code=502, detail="[!] Backend connection error [!]"
                )

            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=504, detail="[!] Backend timeout error [!]"
                )
    def run(self, host="0.0.0.0", port=8000):
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)
