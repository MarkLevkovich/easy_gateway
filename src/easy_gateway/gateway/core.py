import asyncio
import sys
from typing import Any, Dict, Optional, Required, Tuple

import httpx
from fastapi import FastAPI, Request
from fastapi import Response as FastAPIResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from httpx import AsyncClient
from httpx import Response as HTTPXResponse
from loguru import logger
from redis import asyncio as aioredis

from easy_gateway.config import read_config
from easy_gateway.gateway.handler import (
    process_request_middleware,
    process_response_middleware,
)
from easy_gateway.middleware.base import Middleware
from easy_gateway.middleware.logging_middleware import LoggingMiddleware
from easy_gateway.middleware.rate_limit_middleware import RateLimitMiddleware
from easy_gateway.router.router import Router


logger.remove()
logger.add(sys.stderr, format="<cyan>{time:HH:mm:ss}</cyan> | <level>{message}</level>")


class EasyGateway:
    def __init__(self, config_path: str = "config.yaml", config: Dict[str, Any] = None):
        if config is None:
            config = read_config(config_path)

        self.config = config or {}
        self.cache_exp = self.config["redis"].get("expire_time")
        if self.cache_exp is None:
            self.cache_exp = 180

        self.app = FastAPI(title="Easy Gateway")
        self.router = Router()
        self.middlewares: list[Middleware] = []
        self._setup_middleware()
        self._setup_routes()
        self._setup_handler()
        self._setup_cors()
        self._setup_redis()

    def _setup_cors(self):
        cors_config = self.config.get("cors", {})
        if isinstance(cors_config, dict) and "allow_origins" in cors_config:
            allow_conf_origins = cors_config["allow_origins"]
        else:
            allow_conf_origins = ["*"]

        print(f"🔨 Allow origins: {allow_conf_origins}\n")

        self.app.add_middleware(CORSMiddleware, allow_origins=allow_conf_origins)

    def _setup_middleware(self):
        middlewares_config = self.config.get("middlewares", [])

        for mw_config in middlewares_config:
            if not mw_config.get("enabled", True):
                continue

            name = mw_config["name"]
            if name == "LoggingMiddleware":
                self.middlewares.append(LoggingMiddleware())

            elif name == "RateLimitMiddleware":
                rpm = mw_config.get("requests_per_minute", 60)
                self.middlewares.append(RateLimitMiddleware(requests_per_minute=rpm))

            else:
                print(f"🚫 Unknown middleware: {name}")
                # print(f"🚫 Unknown middleware: {name}")

    def _setup_routes(self):
        routes_config = self.config.get("routes")
        if not routes_config:
            print("🚫 No routes configured!")
            return

        # print("🔨 Routes:")
        print("🔨 Routes:")

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
            print(f"- added: {path} -> {target}")

        print("\n")

    def _setup_redis(self):
        redis_setting = self.config.get("redis", {})
        if redis_setting.get("enabled", False):
            redis_url = redis_setting.get("url", "redis://localhost:6379")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                redis = loop.run_until_complete(aioredis.from_url(redis_url))

                loop.run_until_complete(redis.ping())

                FastAPICache.init(RedisBackend(redis), prefix="easy-gateway-cache")
                print(f"✅ Redis cache enabled: {redis_url}")
            except Exception as e:
                print(f"❌ Redis connection error: {e}")
                print("   Start Redis: docker run -d -p 6379:6379 redis")
                print("   Or set redis.enabled: false in config")
                sys.exit(1)
        else:
            FastAPICache.init(InMemoryBackend(), prefix="easy-gateway-cache")
            print("✅ InMemory cache enabled")

    def _setup_handler(self):
        @cache(expire=self.cache_exp)
        @self.app.api_route("/{catch_path:path}", methods=["GET", "POST"])
        async def catch_all(request: Request, catch_path: str):
            logger.debug(f"🎯 HANDLER CALLED: {request.method} {catch_path}")
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

                processed_response = await process_response_middleware(
                    self.middlewares, request, httpx_response
                )

                return processed_response

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
            print(
                "Wrong server configuration, now gateway use standart port(8000) & host(0.0.0.0)"
            )
            # print(f"ERROR: {e}")
        print(f"✅ PORT: {port}, HOST: {host}")

        uvicorn.run(self.app, host=host, port=port, log_level="warning")
