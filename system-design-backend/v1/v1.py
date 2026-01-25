from fastapi import APIRouter
from v1.routes.health_routes import router as health_router
from v1.routes.requests import router as requests_router
from v1.routes.load_test_routes import router as load_test_router

router = APIRouter(prefix="/v1")

router.include_router(health_router, tags=["Health"])
router.include_router(requests_router, tags=["Requests"])
router.include_router(load_test_router, tags=["Load Tests"])
