import base64
import hashlib
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from httpx import AsyncClient
from httpx import Response as HTTPXResponse
from loguru import logger
from redis import asyncio as aioredis

from easy_gateway.config import read_config
from easy_gateway.gateway.admin.router import router as admin_router
from easy_gateway.gateway.handler import (
    process_request_middleware,
    process_response_middleware,
)
from easy_gateway.middleware.base import Middleware
from easy_gateway.middleware.logging_middleware import LoggingMiddleware
from easy_gateway.middleware.rate_limit_middleware import RateLimitMiddleware
from easy_gateway.router.router import Router


# main class
class EasyGateway:
    def __init__(
        self, config_path: str = "easy_conf.yaml", config: dict[str, Any] = None
    ):
        if config is None:
            config = read_config(config_path)

        self.config = config or {}
        self.cache_exp = self.config.get("redis", {}).get("expire_time", 180)

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self._setup_cache()
            self.client = AsyncClient(timeout=30.0)
            yield
            await self.client.aclose()
            if self.redis:
                await self.redis.close()
                logger.info("Redis connection closed")

        self.app = FastAPI(title="Easy Gateway", lifespan=lifespan)
        self.app.state.gateway = self
        self.router = Router()
        self.middlewares: list[Middleware] = []
        self.redis = None
        self.client = None
        self._setup_middleware()
        self._setup_routes()
        self._setup_handler()
        self._setup_cors()

    def _setup_cors(self):
        cors_config = self.config.get("cors", {})
        if isinstance(cors_config, dict) and "allow_origins" in cors_config:
            allow_conf_origins = cors_config["allow_origins"]
        else:
            allow_conf_origins = ["*"]

        logger.info(f"🔨 Allow origins: {allow_conf_origins}\n")

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
                logger.warning(f"🚫 Unknown middleware: {name}")

    def _setup_routes(self):
        routes_config = self.config.get("routes")
        if not routes_config:
            logger.warning("🚫 No routes configured!")
            return

        logger.info("🔨 Routes:")

        for route in routes_config:
            path = route["path"]
            target = route["target"]

            if path.endswith("/*"):
                if "://" not in target:
                    logger.warning(
                        f"🚫 For prefix path: {path} target need to be full URL (with http://)"
                    )
                else:
                    if target.count("/") < 3:
                        logger.warning(
                            f"🚫 For exact route {path} specify full URL with path"
                        )

            self.router.add_route(path, target)
            logger.info(f"- added: {path} -> {target}")

        logger.info("")

    async def _setup_cache(self):
        redis_enabled = self.config.get("redis", {}).get("enabled", False)
        if redis_enabled:
            redis_url = self.config.get("redis", {}).get(
                "url", "redis://localhost:6379"
            )
            try:
                self.redis = await aioredis.from_url(redis_url)
                await self.redis.ping()
                FastAPICache.init(RedisBackend(self.redis), prefix="easy-gateway-cache")
                logger.info(f"✅ Redis cache enabled: {redis_url}")
            except Exception as e:
                logger.error(
                    f"❌ Redis connection error: {e}. Falling back to in-memory cache."
                )
                self.redis = None
                FastAPICache.init(InMemoryBackend(), prefix="easy-gateway-cache")
        else:
            FastAPICache.init(InMemoryBackend(), prefix="easy-gateway-cache")
            logger.info("✅ InMemory cache enabled")

    def check_route_cache(self, path) -> bool:
        redis_enabled = self.config.get("redis", {}).get("enabled", False)
        if redis_enabled:
            routes = self.config.get("routes")
            if not routes:
                return False
            for route in routes:
                if route.get("path") == path:
                    if route.get("cache", False):
                        return True
        return False

    def get_full_route_path(self, path):
        routes = self.config.get("routes", {})
        for route in routes:
            if route.get("path") == path:
                return path
        longest = ""
        for route in routes:
            p = route.get("path")
            if p.endswith("*"):
                p = p.rstrip("*")
            if path.startswith(p):
                if len(p) > len(longest):
                    longest = p
        return longest

    @staticmethod
    def generate_cache_key(path, method, params):
        key = f"{method}:{path}"
        if params:
            key += json.dumps(sorted(params.items()))
        return f"cache:{hashlib.md5(key.encode()).hexdigest()}"

    async def get_cache_data(self, key):
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_cache_data(self, key, data):
        if not self.redis:
            return
        await self.redis.set(key, json.dumps(data), ex=self.cache_exp)

    def _setup_handler(self):
        self.app.include_router(admin_router)

        @self.app.get("/")
        def welcome():
            return {
                "Status": "easy gateway is running",
                "INFO": "admin & docs -> /docs",
            }

        @self.app.get("/health")
        async def check_health():
            checks = {}
            if self.redis is not None:
                try:
                    await self.redis.ping()
                    checks["cache"] = "ok"
                except Exception:
                    checks["cache"] = "unavailable"
            else:
                checks["cache"] = "ok"

            all_ok = all(v == "ok" for v in checks.values())
            return {
                "status": "healthy" if all_ok else "degraded",
                "time": datetime.now().isoformat(),
                "checks": checks,
            }

        # @cache(expire=self.cache_exp)
        @self.app.api_route(
            "/{catch_path:path}",
            methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            include_in_schema=False,
        )
        async def catch_all(request: Request, catch_path: str):
            logger.debug(f"🎯 HANDLER CALLED: {request.method} {catch_path}")
            request, middleware_response = await process_request_middleware(
                self.middlewares, request
            )
            full_path = self.get_full_route_path(catch_path)
            cache_enabled = self.check_route_cache(full_path)
            key = self.generate_cache_key(
                catch_path, request.method, dict(request.query_params)
            )
            if cache_enabled:
                cached = await self.get_cache_data(key)
                if cached:
                    return Response(
                        content=base64.b64decode(cached["body"]),
                        status_code=cached["status_code"],
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

            if "Accept" not in r_headers and "accept" not in r_headers:
                r_headers["Accept"] = "application/json"

            try:
                httpx_response: HTTPXResponse = await self.client.request(
                    method=request.method, url=url, headers=r_headers, content=body
                )

                if (
                    cache_enabled
                    and request.method == "GET"
                    and 200 <= httpx_response.status_code < 300
                ):
                    await self.set_cache_data(
                        key,
                        {
                            "status_code": httpx_response.status_code,
                            "body": base64.b64encode(httpx_response.content).decode(),
                        },
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

    def run(self, config_path: str = "easy_conf.yaml", host="0.0.0.0", port=8000):
        import uvicorn

        try:
            server = self.config.get("server")
            if server is not None:
                host = server["host"]
                port = server["port"]
        except Exception:
            logger.warning(
                "Wrong server configuration, now gateway use standard port(8000) & host(0.0.0.0)"
            )

        logger.info(f"✅ PORT: {port}, HOST: {host}")
        try:
            uvicorn.run(self.app, host=host, port=port, log_level="warning")
        except KeyboardInterrupt:
            logger.info("👋 Shutting down...")
            return
