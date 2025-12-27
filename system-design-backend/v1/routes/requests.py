from fastapi import APIRouter, Request as FastAPIRequest, status
from v1.routes.schema import PostRequestModel, PostResponseModel
import uuid
from datetime import datetime
import hashlib
import json
from v1.services.database_service import db_service
from v1.models.request import Request

router = APIRouter(prefix="/requests")

@router.post("/")
def post_request(request_body: PostRequestModel, request: FastAPIRequest):
    request_uuid = str(uuid.uuid4())
    
    payload_str = json.dumps(request_body.dict(), sort_keys=True)
    payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
    
    request_metadata = Request(
        request_id=request_uuid,
        received_at=datetime.utcnow(),
        endpoint=str(request.url.path),
        method=request.method,
        payload_hash=payload_hash,
        status="received"
    )
    try :
        db_service.create(request_metadata)
    except Exception as e:
        print(e)
        return PostResponseModel(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            status_message="failed",
            request_id=request_uuid
        ) 

    return PostResponseModel(
        status=status.HTTP_200_OK, 
        status_message="received", 
        request_id=request_uuid
    )
