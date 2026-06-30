from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.subscription import SubscriptionStatus, PlanType

class SubscriptionBase(BaseModel):
    plan_type: PlanType

class SubscriptionCreate(SubscriptionBase):
    user_id: int
    stripe_subscription_id: str
    stripe_price_id: str

class SubscriptionUpdate(BaseModel):
    status: Optional[SubscriptionStatus] = None
    cancel_at_period_end: Optional[bool] = None

class SubscriptionResponse(SubscriptionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    stripe_subscription_id: str
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
