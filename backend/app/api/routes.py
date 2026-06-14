from fastapi import APIRouter


# Keep base routes together until the API surface grows enough to split by feature.
router = APIRouter()


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "AI Voice First backend is running"}


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
