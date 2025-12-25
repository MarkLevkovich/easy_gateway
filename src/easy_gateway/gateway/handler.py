from typing import List, Optional, Tuple

from fastapi import Request
from fastapi import Response as FastAPIResponse
from httpx import Response as HTTPXResponse

from easy_gateway.middleware.base import Middleware


async def process_request_middleware(
    middlewares: List[Middleware], request: Request
) -> Tuple[Request, Optional[FastAPIResponse]]:
    for middleware in middlewares:
        result = await middleware.before_request(request)
        if isinstance(result, FastAPIResponse):
            return request, result
        request = result
    return request, None


async def process_response_middleware(
    middlewares: List[Middleware], request: Request, httpx_response: HTTPXResponse
) -> FastAPIResponse:
    fastapi_response = FastAPIResponse(
        content=httpx_response.content,
        status_code=httpx_response.status_code,
        headers=dict(httpx_response.headers),
    )

    for middleware in reversed(middlewares):
        fastapi_response = await middleware.after_response(request, fastapi_response)

    return fastapi_response
