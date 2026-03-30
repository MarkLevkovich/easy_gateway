from fastapi import APIRouter, HTTPException, Request
from loguru import logger

router = APIRouter(prefix="/admin", tags=["Gateway Admin Panel"])
PREFIX = "[ADMIN]"


@router.post("/add_route")
async def add_route(req: Request, path: str, target: str):
    if path.endswith("/*"):
        if "://" not in target:
            detail = f"For prefix path {path}, target must be a full URL (with http://)"
            logger.error(f"{PREFIX} ❌ Bad Request: {detail}")
            raise HTTPException(status_code=400, detail=detail)

        if target.count("/") < 3:
            detail = f"For exact route {path}, specify full URL with path"
            logger.error(f"{PREFIX} ❌ Bad Request: {detail}")
            raise HTTPException(status_code=400, detail=detail)

    gateway = req.app.state.gateway
    gateway.router.add_route(path, target)

    logger.info(f"{PREFIX} ✅ Route added: {path} --> {target}")

    return {"status": "success", "path": path, "target": target}


@router.delete("/del_route")
async def delete_route(req: Request, path: str):
    gateway = req.app.state.gateway
    if gateway.router.delete_route(path):
        logger.info(f"{PREFIX} ✅ route {path} deleted!")
        return {"status": "success", "message": f"Route '{path}' deleted"}

    logger.error(f"{PREFIX} ❌ route {path} not found")
    return {"status": "success", "message": f"Route '{path}' not found"}
