from pydantic import BaseModel
from typing import Optional

class PostRequestModel(BaseModel) :
    rate_of_requests: int
    number_of_requests: int 
    retries_enabled: bool
    rate_limiting: int 
    rate_limiting_algo: str
    cache_enabled: bool
    cache_ttl: int 
    db_latency: int

class PostResponseModel(BaseModel): 
    status: int
    status_message: str
    request_id: str = None
