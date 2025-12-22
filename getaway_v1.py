from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from httpx import AsyncClient

from router_v1 import Router

app = FastAPI(title="Easy Getaway")

router = Router()
router.add_route("/test", "https://httpbin.org")




@app.api_route("/{catch_path:path}", methods=["GET", "POST"])
async def catch_all(request: Request, catch_path: str):
    target = router.find_target(f"/{catch_path}")
    if target:
        url = f"{target}/{catch_path.lstrip('/')}"
        print(url)
    else:
        raise HTTPException(status_code=404)\
        
    body = await request.body()
    r_headers = dict(request.headers)

    async with AsyncClient() as client:
        response = await client.request(
            method=request.method, url=url, headers=r_headers, content=body
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
