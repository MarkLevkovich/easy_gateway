import time
import sys
from loguru import logger

# Настроить один раз
from fastapi import Request, Response

from easy_gateway.middleware.base import Middleware

logger.remove()  # убрать стандартный вывод
logger.add(
    sys.stderr, format="<cyan>{time:HH:mm:ss}</cyan> | <level>{message}</level>"
)

class LoggingMiddleware(Middleware):
    async def before_request(self, req: Request):
        req.state.start_time = time.time()
        logger.debug(f"🫣Request! Path -> {req.url.path}, method -> {req.method}.")
        return req

    async def after_response(self, req: Request, res: Response):
        elapsed = time.time() - req.state.start_time
        logger.debug(
            f"🥳All Done! Response status-code -> {res.status_code}, time -> {elapsed}."
        )
        return res
