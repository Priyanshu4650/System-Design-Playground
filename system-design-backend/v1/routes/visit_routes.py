from fastapi import APIRouter, Request
from v1.services.database_service_traced import db_service_traced as db_service
from sqlalchemy import text
from datetime import datetime

router = APIRouter(prefix="/visits")

@router.post("/track")
async def track_visit(request: Request):
    """Track a page visit"""
    visitor_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    with db_service.get_session() as session:
        # Record the visit
        session.execute(
            text("INSERT INTO page_visits (visitor_ip, user_agent) VALUES (:ip, :ua)"),
            {"ip": visitor_ip, "ua": user_agent}
        )
        
        # Update stats
        session.execute(
            text("UPDATE visit_stats SET total_visits = total_visits + 1, last_updated = :now WHERE id = 1"),
            {"now": datetime.utcnow()}
        )
        
        # Update unique visitors count
        unique_count = session.execute(
            text("SELECT COUNT(DISTINCT visitor_ip) FROM page_visits")
        ).scalar()
        
        session.execute(
            text("UPDATE visit_stats SET unique_visitors = :count WHERE id = 1"),
            {"count": unique_count}
        )
        
        session.commit()
    
    return {"status": "tracked"}

@router.get("/stats")
async def get_visit_stats():
    """Get visit statistics"""
    with db_service.get_session() as session:
        result = session.execute(
            text("SELECT total_visits, unique_visitors FROM visit_stats WHERE id = 1")
        ).fetchone()
        
        if result:
            return {
                "total_visits": result[0],
                "unique_visitors": result[1]
            }
        
@router.get("/admin")
async def get_admin_stats(password: str = None):
    """Get detailed admin statistics"""
    if password != "admin123":  # Simple password check
        return {"error": "Unauthorized"}
    
    with db_service.get_session() as session:
        # Get visit stats
        visit_stats = session.execute(
            text("SELECT total_visits, unique_visitors FROM visit_stats WHERE id = 1")
        ).fetchone()
        
        # Get recent visits
        recent_visits = session.execute(
            text("SELECT visitor_ip, user_agent, visited_at FROM page_visits ORDER BY visited_at DESC LIMIT 20")
        ).fetchall()
        
        # Get load test stats
        test_stats = session.execute(
            text("SELECT COUNT(*) as total_tests, COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed FROM test_runs")
        ).fetchone()
        
        return {
            "visit_stats": {
                "total_visits": visit_stats[0] if visit_stats else 0,
                "unique_visitors": visit_stats[1] if visit_stats else 0
            },
            "recent_visits": [
                {
                    "ip": visit[0],
                    "user_agent": visit[1],
                    "visited_at": visit[2]
                } for visit in recent_visits
            ],
            "test_stats": {
                "total_tests": test_stats[0] if test_stats else 0,
                "completed_tests": test_stats[1] if test_stats else 0
            }
        }
        
@router.get("/admin/download")
async def download_database(password: str = None):
    """Download database data as JSON"""
    from fastapi.responses import JSONResponse
    import json
    
    if password != "admin123":
        return {"error": "Unauthorized"}
    
    with db_service.get_session() as session:
        # Get all data
        visits = session.execute(text("SELECT * FROM page_visits")).fetchall()
        test_runs = session.execute(text("SELECT * FROM test_runs")).fetchall()
        test_requests = session.execute(text("SELECT * FROM test_requests")).fetchall()
        
        data = {
            "export_date": datetime.utcnow().isoformat(),
            "page_visits": [dict(row._mapping) for row in visits],
            "test_runs": [dict(row._mapping) for row in test_runs],
            "test_requests": [dict(row._mapping) for row in test_requests]
        }
        
        return JSONResponse(
            content=data,
            headers={"Content-Disposition": "attachment; filename=database_export.json"}
        )