from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import TypeVar, Type, List, Optional
import os
from v1.models.request import Request
from v1.services.observability import logger
from tracing.trace_decorators import trace_operation
from models.tracing.trace_models import EventType

T = TypeVar('T')

class DatabaseServiceWithTracing:
    def __init__(self):
        # Use SQLite with persistent storage in container
        db_path = os.path.join('/app/data', 'load_test.db')
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_db()
        logger.info(f"SQLite database initialized at {db_path}")
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    @trace_operation(EventType.DB_CALL_STARTED, lambda *args, **kwargs: {"operation": "create"})
    def create(self, obj: T, request_id: str = None, session: Optional[Session] = None) -> T:
        if session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
        with self.get_session() as db:
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj
    
    @trace_operation(EventType.DB_CALL_STARTED, lambda *args, **kwargs: {"operation": "get_by_idempotency_key"})
    def get_by_idempotency_key(self, idempotency_key: str, request_id: str = None, session: Optional[Session] = None) -> Optional[Request]:
        if session:
            return session.query(Request).filter(Request.idempotency_key == idempotency_key).first()
        with self.get_session() as db:
            return db.query(Request).filter(Request.idempotency_key == idempotency_key).first()
    
    @trace_operation(EventType.DB_CALL_STARTED, lambda *args, **kwargs: {"operation": "query"})
    def query(self, model_class: Type[T], request_id: str = None, session: Optional[Session] = None) -> List[T]:
        if session:
            return session.query(model_class).all()
        with self.get_session() as db:
            return db.query(model_class).all()
    
    @trace_operation(EventType.DB_CALL_STARTED, lambda *args, **kwargs: {"operation": "update"})
    def update(self, obj: T, request_id: str = None, session: Optional[Session] = None) -> T:
        if session:
            session.merge(obj)
            session.commit()
            return obj
        with self.get_session() as db:
            db.merge(obj)
            db.commit()
            return obj

    def init_db(self):
        # Initialize main schema
        schema_path = os.path.join(os.path.dirname(__file__), '../../sqlite_schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.engine.connect() as conn:
                conn.execute(text(schema_sql))
                conn.commit()
        
        # Initialize load test schema
        load_test_schema_path = os.path.join(os.path.dirname(__file__), '../../sqlite_load_test_schema.sql')
        if os.path.exists(load_test_schema_path):
            with open(load_test_schema_path, 'r') as f:
                load_test_schema_sql = f.read()
            
            with self.engine.connect() as conn:
                # Execute each statement separately for SQLite
                statements = [stmt.strip() for stmt in load_test_schema_sql.split(';') if stmt.strip()]
                for statement in statements:
                    conn.execute(text(statement))
                conn.commit()
        
        # Initialize visit tracking schema
        visit_schema_path = os.path.join(os.path.dirname(__file__), '../../visit_tracking_schema.sql')
        if os.path.exists(visit_schema_path):
            with open(visit_schema_path, 'r') as f:
                visit_schema_sql = f.read()
            
            with self.engine.connect() as conn:
                statements = [stmt.strip() for stmt in visit_schema_sql.split(';') if stmt.strip()]
                for statement in statements:
                    conn.execute(text(statement))
                conn.commit()
                
                # Initialize visit stats if not exists
                conn.execute(text("INSERT OR IGNORE INTO visit_stats (id, total_visits, unique_visitors) VALUES (1, 0, 0)"))
                conn.commit()

db_service_traced = DatabaseServiceWithTracing()