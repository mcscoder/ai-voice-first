from fastapi import FastAPI

from app.api.routes import router
from app.core.config import APP_HOST, APP_PORT, APP_TITLE, APP_VERSION


app = FastAPI(title=APP_TITLE, version=APP_VERSION)
app.include_router(router)


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)


if __name__ == "__main__":
    main()
