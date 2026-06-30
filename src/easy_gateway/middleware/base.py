from fastapi import Request
from fastapi import Response as FastAPIResponse


class Middleware:
    async def before_request(self, req: Request) -> Request:
        # some code...
        return req

    async def after_response(
        self, req: Request, res: FastAPIResponse
    ) -> FastAPIResponse:
        # some code...
        return res
