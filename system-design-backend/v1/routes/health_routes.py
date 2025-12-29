from fastapi import APIRouter, status
from v1.routes.schema import PostResponseModel
from v1.services.observability import logger

router = APIRouter(prefix="/health")

@router.get("/")
def read_root():
    logger.info("health check", endpoint="/health", method="GET")
    return PostResponseModel(
        status=status.HTTP_200_OK, 
        status_message="healthy"
    )