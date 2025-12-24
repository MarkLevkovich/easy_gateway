import time
from fastapi import Request, Response
from middleware.base import Middleware


class LoggingMiddleware(Middleware):
    async def before_request(self, req: Request):
        req.state.start_time = time.time()
        print(f"🫣Requset! Path -> {req.url.path}, method -> {req.method}.")
        return req
        
    async def after_response(self,req: Request, res: Response):
        elapsed = time.time() - req.state.start_time
        print(f"🥳All Done! Response status-code -> {res.status_code}, time -> {elapsed}.")
        return res