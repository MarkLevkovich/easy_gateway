from typing import Any, Dict, Optional, Required, Tuple

import httpx
from fastapi import FastAPI, Request
from fastapi import Response as FastAPIResponse
from fastapi.exceptions import HTTPException
from httpx import AsyncClient
from httpx import Response as HTTPXResponse

from easy_gateway.config import read_config
from easy_gateway.gateway.handler import (
    process_request_middleware,
    process_response_middleware,
)
from easy_gateway.middleware.base import Middleware
from easy_gateway.middleware.logging_middleware import LoggingMiddleware
from easy_gateway.middleware.rate_limit_middleware import RateLimitMiddleware
from easy_gateway.router.router import Router


class EasyGateway:
    def __init__(self, config_path: str = "config.yaml", config: Dict[str, Any] = None):
        # check config
        if config is None:
            config = read_config(config_path)

        self.config = config or {}

        # init basics apps
        self.app = FastAPI(title="Easy Gateway")
        self.router = Router()
        self.middlewares: list[Middleware] = []
        self._setup_middleware()
        self._setup_routes()
        self._setup_handler()

    def _setup_middleware(self):
        middlewares_config = self.config.get("middlewares", [])

        for mw_config in middlewares_config:
            if not mw_config.get("enebled", True):
                continue

            name = mw_config["name"]
            if name == "LoggingMiddleware":
                self.middlewares.append(LoggingMiddleware())

            elif name == "RateLimitMiddleware":
                rpm = mw_config.get("requests_per_minute", 60)
                self.middlewares.append(RateLimitMiddleware(requests_per_minute=rpm))

            else:
                print(f"🚫 Unknown middleware: {name}")

    def _setup_routes(self):
        routes_config = self.config.get("routes")
        if not routes_config:
            print("🚫 No routes configured!")
            return

        for route in routes_config:
            path = route["path"]
            target = route["target"]

            if path.endswith("/*"):
                if "://" not in target:
                    print(
                        f"🚫 For prefix path: {path} target need to be full URL (with http://)"
                    )
                else:
                    if target.count("/") < 3:
                        print(f"🚫 For exact route {path} specify full URL with path")

            self.router.add_route(path, target)
            print(f"✅ Route added: {path} -> {target}")

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

    def run(self, config_path: str = "config.yaml", host="0.0.0.0", port=8000):
        import uvicorn
        try:
            server = self.config.get("server")
            if server is not None:
                host = server["host"]
                port = server["port"]
        except Exception as e:
            print("Wrong server configuration, now gateway use standart port(8000) & host(0.0.0.0)")
            # print(f"ERROR: {e}")

        uvicorn.run(self.app, host=host, port=port)
