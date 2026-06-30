from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...database import get_db
from ...models.user import User
from ...models.subscription import Subscription, SubscriptionStatus
from ...schemas.subscription import SubscriptionResponse, SubscriptionCreate
from .auth import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("/my-subscription", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        plan_type=subscription.plan_type,
        stripe_subscription_id=subscription.stripe_subscription_id,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        created_at=subscription.created_at
    )

@router.post("/create", response_model=dict)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if user already has a subscription
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a subscription"
        )
    
    # Create new subscription
    new_subscription = Subscription(
        user_id=current_user.id,
        stripe_subscription_id=subscription_data.stripe_subscription_id,
        stripe_price_id=subscription_data.stripe_price_id,
        plan_type=subscription_data.plan_type,
        status=SubscriptionStatus.ACTIVE
    )
    
    # Update user's plan
    current_user.plan = subscription_data.plan_type
    current_user.stripe_subscription_id = subscription_data.stripe_subscription_id
    
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    
    return {
        "message": "Subscription created successfully",
        "subscription_id": new_subscription.id
    }

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    subscription.cancel_at_period_end = True
    subscription.status = SubscriptionStatus.CANCELLED
    
    db.commit()
    
    return {"message": "Subscription cancelled successfully"}
