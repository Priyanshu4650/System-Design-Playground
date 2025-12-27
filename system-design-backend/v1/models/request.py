from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Request(Base):
    __tablename__ = "requests"
    
    request_id = Column(String, primary_key=True)
    received_at = Column(DateTime, nullable=False)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)
    idempotency_key = Column(String)
    status = Column(String, nullable=False)
    latency_ms = Column(Integer)
    retry_count = Column(Integer, default=0)