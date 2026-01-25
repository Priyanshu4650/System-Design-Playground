from fastapi import APIRouter, HTTPException, status, Request
from v1.models.load_test import LoadTestRequest, LoadTestResult, LoadTestStatus, TestStatus
from v1.services.load_test_service import load_test_service
from v1.services.observability import logger
import json

router = APIRouter(prefix="/tests")

@router.post("/start", response_model=LoadTestStatus)
async def start_load_test(request_body: LoadTestRequest, request: Request):
    """Start a new load test"""
    try:
        # Debug: Print raw request body
        body = await request.body()
        print(f"DEBUG: Raw request body: {body.decode()}")
        
        print(f"DEBUG: Parsed request: {request_body}")
        print(f"DEBUG: Request dict: {request_body.dict()}")
        
        # Validate configuration
        config = request_body.config
        print(f"DEBUG: Config: {config}")
        print(f"DEBUG: Config dict: {config.dict()}")
        
        # Ensure either total_requests or (rps + duration) is provided
        if not config.total_requests and not (config.rps and config.duration):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either total_requests or both rps and duration"
            )
        
        print("DEBUG: Starting load test service")
        # Start the test
        test_id = await load_test_service.start_test(config)
        print(f"DEBUG: Test started with ID: {test_id}")
        
        return LoadTestStatus(
            test_id=test_id,
            status=TestStatus.PENDING,
            progress={"message": "Test started, executing in background"}
        )
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start load test: {str(e)}"
        )

@router.get("/{test_id}/result", response_model=LoadTestResult)
async def get_load_test_result(test_id: str):
    """Get load test result by test_id"""
    try:
        result = await load_test_service.get_test_result(test_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Load test {test_id} not found"
            )
        
        # Convert database result to response model
        return LoadTestResult(
            test_id=result["test_id"],
            status=TestStatus(result["status"]),
            total_requests=result.get("total_requests", 0),
            succeeded=result.get("succeeded", 0),
            failed=result.get("failed", 0),
            rate_limited=result.get("rate_limited", 0),
            duplicates=result.get("duplicates", 0),
            retries_total=result.get("retries_total", 0),
            avg_latency_ms=result.get("avg_latency_ms"),
            p95_latency_ms=result.get("p95_latency_ms"),
            p99_latency_ms=result.get("p99_latency_ms"),
            start_time=result.get("started_at"),
            end_time=result.get("completed_at"),
            duration_sec=result.get("duration_sec")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("load_test_result_fetch_failed", test_id=test_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch test result: {str(e)}"
        )

@router.get("/{test_id}/status", response_model=LoadTestStatus)
async def get_load_test_status(test_id: str):
    """Get current status of a load test"""
    try:
        result = await load_test_service.get_test_result(test_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Load test {test_id} not found"
            )
        
        progress = None
        if result["status"] == TestStatus.RUNNING.value:
            # Could add progress tracking here
            progress = {"message": "Test is running"}
        elif result["status"] == TestStatus.COMPLETED.value:
            progress = {
                "message": "Test completed",
                "succeeded": result.get("succeeded", 0),
                "failed": result.get("failed", 0)
            }
        
        return LoadTestStatus(
            test_id=test_id,
            status=TestStatus(result["status"]),
            progress=progress
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("load_test_status_fetch_failed", test_id=test_id, error=str(e))
@router.get("/{test_id}/download")
async def download_test_result(test_id: str):
    """Download test result as JSON"""
    from fastapi.responses import JSONResponse
    
    try:
        result = await load_test_service.get_test_result(test_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Load test {test_id} not found"
            )
        
        return JSONResponse(
            content=result,
            headers={"Content-Disposition": f"attachment; filename=load_test_{test_id}.json"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download test result: {str(e)}"
        )

@router.post("/{test_id}/email")
async def email_test_result(test_id: str, email: str):
    """Email test result (mock implementation)"""
    try:
        result = await load_test_service.get_test_result(test_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Load test {test_id} not found"
            )
        
        # Mock email sending - in production, use actual email service
        print(f"MOCK EMAIL: Sending test result {test_id} to {email}")
        print(f"Result summary: {result.get('succeeded', 0)} succeeded, {result.get('failed', 0)} failed")
        
        return {"message": f"Test result sent to {email}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to email test result: {str(e)}"
        )