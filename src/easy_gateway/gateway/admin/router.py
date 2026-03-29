from fastapi import APIRouter, Request
from loguru import logger

router = APIRouter(prefix="/admin", tags=["Gateway Admin Panel"])


@router.post("/add_route")
async def add_route(req: Request, path: str, target: str):
    if path.endswith("/*"):
        if "://" not in target:
            logger.warning(
                f"🚫 For prefix path: {path} target need to be full URL (with http://)"
            )
        else:
            if target.count("/") < 3:
                logger.warning(f"🚫 For exact route {path} specify full URL with path")
    gateway = req.app.state.gateway
    gateway.router.add_route(path, target)
    logger.info(f"Added {path} route --> {target}")
