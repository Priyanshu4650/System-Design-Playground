from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tracing.trace_middleware import TracingMiddleware
from v1.v1 import router as v1_router
from v1.routes.requests import router as requests_router
from v1.routes.trace_routes import router as trace_router
from v1.routes.metrics import router as metrics_router
from v1.routes.websocket import router as websocket_router
from v1.routes.config import router as config_router
from startup import initialize_system, log_system_status

# Initialize system before creating FastAPI app
initialize_system()

app = FastAPI(title="System Design Playground", version="1.0.0")

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TracingMiddleware)

# Include routers
app.include_router(v1_router)
app.include_router(requests_router)
app.include_router(trace_router)
app.include_router(metrics_router)
app.include_router(websocket_router)
app.include_router(config_router)

@app.on_event("startup")
async def startup_event():
    """Log system status on FastAPI startup"""
    log_system_status()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": ["redis", "database", "cache", "tracing"],
        "failure_injection": "enabled",
        "tracing": "enabled",
        "caching": "enabled"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
