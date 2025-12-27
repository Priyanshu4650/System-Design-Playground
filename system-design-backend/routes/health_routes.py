from fastapi import APIRouter, status

router = APIRouter("/health")

@router.get("/")
def read_root():
    return {
        "status": status.HTTP_200_OK,
        "message": "OK",
        "data": {}
    }