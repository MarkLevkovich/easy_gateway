from fastapi import FastAPI, Request, Response
from httpx import AsyncClient


app = FastAPI(title="Easy Getaway")

TEST_TARGET = "https://httpbin.org/"

@app.api_route("/{catch_path:path}", methods=["GET", "POST"])
async def cath_all(request: Request, catch_path: str):
    url = f"{TEST_TARGET}/{catch_path}"
    body = await request.body()
    r_headers =dict(request.headers)
    
    async with AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=r_headers,
            content=body
        )
        
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
    
    

    