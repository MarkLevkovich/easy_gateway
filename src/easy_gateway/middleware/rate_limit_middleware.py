import time
from collections import defaultdict
from typing import Any, Dict, List

from fastapi import Request
from fastapi.responses import JSONResponse

from easy_gateway.middleware.base import Middleware


class RateLimitMiddleware(Middleware):
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def _clean_old_requests(self, ip):
        now = time.time()
        time_minute_ago = now - 60

        self.requests[ip] = [
            timestamp for timestamp in self.requests[ip] if timestamp > time_minute_ago
        ]

    def get_client_ip(self, req: Request):
        if req.client is None:
            return "unknown"
        return req.client.host

    async def before_request(self, req: Request) -> Any:
        ip = self.get_client_ip(req)

        self._clean_old_requests(ip)

        if len(self.requests[ip]) >= self.requests_per_minute:
            return JSONResponse(
                content={"Error": "too many requests"},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        self.requests[ip].append(time.time())

        return req
