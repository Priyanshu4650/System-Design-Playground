from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import TypeVar, Type, List, Optional
import os
import logging
from v1.models.request import Request
import time
from v1.services.observability import logger

T = TypeVar('T')

class DatabaseService:
    def __init__(self, host: str, password: str, database: str, username: str, port: int = 5432):
        self.engine = create_engine(f"postgresql://{username}:{password}@{host}:{port}/{database}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_db()
        logger.info("Database initialized")

    def _simulate_testing(self, testing: bool = True, sleep_time: float = 2.0):
        if testing:
            time.sleep(sleep_time)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def query(self, model_class: Type[T], db_latency_ms: int = 2000, session: Optional[Session] = None) -> List[T]:
        self._simulate_testing(True, db_latency_ms / 1000.0) 
        if session:
            return session.query(model_class).all()
        with self.get_session() as db:
            return db.query(model_class).all()
    
    def get_by_id(self, model_class: Type[T], id: int, db_latency_ms: int = 2000, session: Optional[Session] = None) -> Optional[T]:
        self._simulate_testing(True, db_latency_ms / 1000.0) 
        if session:
            return session.query(model_class).filter(model_class.id == id).first()
        with self.get_session() as db:
            return db.query(model_class).filter(model_class.id == id).first()
    
    def create(self, obj: T, db_latency_ms: int = 2000, session: Optional[Session] = None) -> T:
        self._simulate_testing(True, db_latency_ms / 1000.0) 
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
    
    def update(self, obj: T, db_latency_ms: int = 2000, session: Optional[Session] = None) -> T:
        self._simulate_testing(True, db_latency_ms / 1000.0)
        if session:
            session.merge(obj)
            session.commit()
            return obj
        with self.get_session() as db:
            db.merge(obj)
            db.commit()
            return obj
    
    def delete(self, model_class: Type[T], id: int, db_latency_ms: int = 2000, session: Optional[Session] = None) -> bool:
        self._simulate_testing(True, db_latency_ms / 1000.0) 
        if session:
            obj = session.query(model_class).filter(model_class.id == id).first()
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        with self.get_session() as db:
            obj = db.query(model_class).filter(model_class.id == id).first()
            if obj:
                db.delete(obj)
                db.commit()
                return True
            return False

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
                
    def get_by_idempotency_key(self, idempotency_key: str, db_latency_ms: int = 2000, session: Optional[Session] = None) -> Optional[Request]:
        self._simulate_testing(True, db_latency_ms / 1000.0) 
        if session:
            return session.query(Request).filter(Request.idempotency_key == idempotency_key).first()
        with self.get_session() as db:
            return db.query(Request).filter(Request.idempotency_key == idempotency_key).first()


            
db_service = DatabaseService(
    host="localhost",
    password="password",
    username="postgres",
    database="system-design-playground"
)