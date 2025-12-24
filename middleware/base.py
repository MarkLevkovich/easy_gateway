from fastapi import Request, Response


class Middleware:
    
    async def before_request(self, req: Request):
        # some code...
        return req
        
    async def after_response(self,req: Request, res: Response):
        # some code...
        return res