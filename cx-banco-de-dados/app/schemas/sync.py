from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class SyncEvent(BaseModel):
    entity_type: str  # user_settings, conversation, message, etc.
    entity_id: Optional[int] = None
    changes: Dict[str, Any]
    action: str = "update"  # create, update, delete
