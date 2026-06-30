from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from ...database import get_db
from ...models.user import User, PlanType
from ...models.token_usage import TokenUsage
from ...schemas.token import TokenUsageCreate, TokenUsageResponse, TokenUsageStats
from ...config import get_settings
from .auth import get_current_user

router = APIRouter(prefix="/tokens", tags=["Tokens"])
settings = get_settings()

def get_token_limit(plan: PlanType) -> int:
    """Get token limit based on user plan"""
    limits = {
        PlanType.FREE: settings.FREE_TOKENS_PER_DAY,
        PlanType.PRO: settings.PRO_TOKENS_PER_DAY,
        PlanType.MAX: settings.MAX_TOKENS_PER_DAY
    }
    return limits.get(plan, settings.FREE_TOKENS_PER_DAY)

@router.post("/usage", response_model=TokenUsageResponse)
async def log_token_usage(
    usage: TokenUsageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user has exceeded their limit
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_usage = db.query(TokenUsage).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.date >= today_start
    ).all()
    
    total_tokens_today = sum(u.total_tokens for u in today_usage)
    token_limit = get_token_limit(current_user.plan)
    
    if total_tokens_today + usage.input_tokens + usage.output_tokens > token_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Token limit exceeded. Limit: {token_limit}, Used: {total_tokens_today}"
        )
    
    # Create token usage record
    new_usage = TokenUsage(
        user_id=current_user.id,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.input_tokens + usage.output_tokens,
        model_id=usage.model_id,
        endpoint=usage.endpoint
    )
    
    # Update user's daily counter
    current_user.tokens_used_today += new_usage.total_tokens
    
    db.add(new_usage)
    db.commit()
    db.refresh(new_usage)
    
    return TokenUsageResponse(
        id=new_usage.id,
        user_id=new_usage.user_id,
        model_id=new_usage.model_id,
        input_tokens=new_usage.input_tokens,
        output_tokens=new_usage.output_tokens,
        total_tokens=new_usage.total_tokens,
        cost=new_usage.cost,
        created_at=new_usage.created_at
    )

@router.get("/stats", response_model=TokenUsageStats)
async def get_token_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Today's usage
    today_usage = db.query(TokenUsage).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.date >= today_start
    ).all()
    
    # This month's usage
    month_usage = db.query(TokenUsage).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.date >= month_start
    ).all()
    
    total_tokens_today = sum(u.total_tokens for u in today_usage)
    total_tokens_month = sum(u.total_tokens for u in month_usage)
    total_cost_today = sum(u.cost for u in today_usage)
    
    token_limit = get_token_limit(current_user.plan)
    remaining_tokens = max(0, token_limit - total_tokens_today)
    
    return TokenUsageStats(
        total_tokens_today=total_tokens_today,
        total_tokens_this_month=total_tokens_month,
        total_cost_today=total_cost_today,
        remaining_tokens=remaining_tokens
    )

@router.get("/history")
async def get_token_history(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    usage_records = db.query(TokenUsage).filter(
        TokenUsage.user_id == current_user.id,
        TokenUsage.date >= start_date
    ).order_by(TokenUsage.date.desc()).limit(100).all()
    
    return [
        {
            "id": u.id,
            "model_id": u.model_id,
            "total_tokens": u.total_tokens,
            "cost": u.cost,
            "created_at": u.created_at
        }
        for u in usage_records
    ]
