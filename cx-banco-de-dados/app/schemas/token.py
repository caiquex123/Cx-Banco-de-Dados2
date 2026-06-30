from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class TokenUsageBase(BaseModel):
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0

class TokenUsageCreate(TokenUsageBase):
    user_id: int
    endpoint: Optional[str] = None

class TokenUsageResponse(TokenUsageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    total_tokens: int
    cost: float = 0.0
    created_at: datetime

class TokenUsageStats(BaseModel):
    total_tokens_today: int = 0
    total_tokens_this_month: int = 0
    total_cost_today: float = 0.0
    remaining_tokens: int = 0
