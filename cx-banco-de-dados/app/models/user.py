from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ..database import Base

class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    MAX = "max"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Plano atual
    plan = Column(Enum(PlanType), default=PlanType.FREE)
    
    # Stripe
    stripe_customer_id = Column(String(255), unique=True, nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    subscription_status = Column(String(50), default="inactive")
    
    # Tokens
    tokens_used_today = Column(Integer, default=0)
    tokens_reset_at = Column(DateTime, default=func.now())
    
    # API Key
    api_key = Column(String(255), unique=True, nullable=True)
    api_key_hash = Column(String(255), nullable=True)
    
    # Metadata
    metadata_json = Column(JSON, default=dict)
    settings_json = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships - defined after all models are imported
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    token_usage_logs = relationship("TokenUsage", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, plan={self.plan})>"
