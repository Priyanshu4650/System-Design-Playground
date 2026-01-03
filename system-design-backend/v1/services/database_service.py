from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import TypeVar, Type, List, Optional
import os
import logging
from v1.models.request import Request
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DatabaseService:
    def __init__(self, host: str, password: str, database: str, username: str, port: int = 5432):
        self.engine = create_engine(f"postgresql://{username}:{password}@{host}:{port}/{database}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_db()
        logger.info("Database initialized")

    def _simulate_testing(self, testing: bool = True, sleep_time: int = 2) :
        if testing :
            time.sleep(sleep_time)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def query(self, model_class: Type[T], session: Optional[Session] = None) -> List[T]:
        self._simulate_testing(1)
        if session:
            return session.query(model_class).all()
        with self.get_session() as db:
            return db.query(model_class).all()
    
    def get_by_id(self, model_class: Type[T], id: int, session: Optional[Session] = None) -> Optional[T]:
        self._simulate_testing(1.5)
        if session:
            return session.query(model_class).filter(model_class.id == id).first()
        with self.get_session() as db:
            return db.query(model_class).filter(model_class.id == id).first()
    
    def create(self, obj: T, session: Optional[Session] = None) -> T:
        self._simulate_testing(0.75)
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
    
    def update(self, obj: T, session: Optional[Session] = None) -> T:
        self._simulate_testing()
        if session:
            session.merge(obj)
            session.commit()
            return obj
        with self.get_session() as db:
            db.merge(obj)
            db.commit()
            return obj
    
    def delete(self, model_class: Type[T], id: int, session: Optional[Session] = None) -> bool:
        self._simulate_testing(1)
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
                
    def get_by_idempotency_key(self, idempotency_key: str, session: Optional[Session] = None) -> Optional[Request]:
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