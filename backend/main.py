from fastapi import FastAPI

from app.api.routes import router
from app.core.config import config


# Build the FastAPI application and register project routes.
app = FastAPI(title=config.title, version=config.version)
app.include_router(router)


def main() -> None:
    import uvicorn

    # Run the API from Python so deployment does not depend on a uvicorn CLI command.
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
