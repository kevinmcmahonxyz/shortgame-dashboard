from fastapi import APIRouter

from backend.services.stats_service import compute_stats

router = APIRouter()


@router.get("/api/stats")
def get_stats():
    return compute_stats()
