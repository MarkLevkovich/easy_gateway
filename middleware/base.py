from typing import Optional, Tuple
from fastapi import Request, Response as FastAPIResponse
from httpx import Response as HTTPXResponse


class Middleware:
    
    async def before_request(self, req: Request):
        # some code...
        return req
        
    async def after_response(self,req: Request, res: FastAPIResponse):
        # some code...
        return res