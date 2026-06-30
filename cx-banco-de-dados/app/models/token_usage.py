from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class TokenUsage(Base):
    __tablename__ = "token_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Contagem
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Custo
    cost = Column(Float, default=0.0)
    
    # Modelo usado
    model_id = Column(String(100), nullable=False)
    
    # Request info
    request_id = Column(String(255), unique=True, nullable=True)
    endpoint = Column(String(255), nullable=True)
    metadata_json = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="token_usage_logs")
    
    def __repr__(self):
        return f"<TokenUsage(id={self.id}, user_id={self.user_id}, tokens={self.total_tokens})>"
