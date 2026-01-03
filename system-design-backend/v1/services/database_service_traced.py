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
    def __init__(self, host: str, password: str, database: str, username: str, port: int = 5432):
        self.engine = create_engine(f"postgresql://{username}:{password}@{host}:{port}/{database}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_db()
        logger.info("Database initialized with tracing")
    
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
        schema_path = os.path.join(os.path.dirname(__file__), '../../schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'requests')"
                ))
                if not result.scalar():
                    conn.execute(text(schema_sql))
                    conn.commit()

db_service_traced = DatabaseServiceWithTracing(
    host="localhost",
    password="password",
    username="postgres",
    database="system-design-playground"
)