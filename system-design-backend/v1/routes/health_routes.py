from fastapi import APIRouter, status
from v1.routes.schema import PostResponseModel

router = APIRouter(prefix="/health")

@router.get("/")
def read_root():
    return PostResponseModel(
        status=status.HTTP_200_OK, 
        status_message="healthy"
    )