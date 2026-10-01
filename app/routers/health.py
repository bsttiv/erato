from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check():
    """Liveness check endpoint.

    Returns structured status without performing any database round trip.
    """
    return {"status": "ok"}
