from fastapi import FastAPI, Request


app = FastAPI(title="Easy Getaway")


@app.api_route("/{catch_path:path}", methods=["GET", "POST"])
async def cath_all(request: Request, catch_path: str):
    # tests
    print(f"Метод: {request.method}")
    print(f"URL: {request.url}")
    print(f"Заголовки: {request.headers}")
    body = await request.body()
    print(f"Тело: {body}")

    