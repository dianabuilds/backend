from fastapi import APIRouter

# Subrouters will be included by the aggregator in http.py of this package.

router = APIRouter(prefix="/api/moderation", tags=["moderation"])

__all__ = ["router"]
