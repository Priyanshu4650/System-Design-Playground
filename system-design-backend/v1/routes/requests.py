from fastapi import APIRouter, Request as FastAPIRequest, status
from v1.routes.schema import PostRequestModel, PostResponseModel
import uuid
import time
from datetime import datetime
import hashlib
import json
from v1.services.database_service import db_service
from v1.models.request import Request
from v1.services.observability import logger, log_request

router = APIRouter(prefix="/requests")

@router.post("/")
def post_request(request_body: PostRequestModel, request: FastAPIRequest):
    start_time = time.time()
    request_uuid = str(uuid.uuid4())

    logger.info("request started", request_id=request_uuid, endpoint=str(request.url.path), method=request.method)
    
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
        duration = time.time() - start_time
        log_request(request_uuid, str(request.url.path), request.method, status.HTTP_200_OK, duration)
        
        return PostResponseModel(
            status=status.HTTP_200_OK, 
            status_message="received", 
            request_id=request_uuid
        )
        logger.info("request completed", request_id=request_uuid, endpoint=str(request.url.path), method=request.method)
    except Exception as e:
        duration = time.time() - start_time
        logger.error("request failed", request_id=request_uuid, endpoint=str(request.url.path), method=request.method, error=str(e))
        log_request(request_uuid, str(request.url.path), request.method, status.HTTP_500_INTERNAL_SERVER_ERROR, duration)
        return PostResponseModel(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            status_message="failed",
            request_id=request_uuid
        ) 

