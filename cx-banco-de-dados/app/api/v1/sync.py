from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header
from sqlalchemy.orm import Session
from datetime import datetime
from ...database import get_db
from ...models.user import User
from ...core.websocket import ConnectionManager
from ...schemas.sync import SyncEvent
from ...core.security import hash_api_key

router = APIRouter(prefix="/sync", tags=["Auto-Sync"])
manager = ConnectionManager()

async def get_api_key_header(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    return x_api_key

@router.post("/auto-sync")
async def auto_sync_database(
    event: SyncEvent,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key_header)
):
    """
    Auto-sincronização: Quando algo muda no frontend,
    atualiza automaticamente no banco de dados
    """
    user = db.query(User).filter(User.api_key_hash == hash_api_key(api_key)).first()
    if not user:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    # Processa o evento de sync
    if event.entity_type == "user_settings":
        user.settings_json = {**user.settings_json, **event.changes}
    
    elif event.entity_type == "conversation":
        from ...models.conversation import Conversation
        if event.action == "create":
            # Create new conversation
            conv = Conversation(
                user_id=user.id,
                title=event.changes.get("title"),
                model_used=event.changes.get("model_used", "default"),
                metadata_json=event.changes.get("metadata", {}),
                settings_json=event.changes.get("settings", {})
            )
            db.add(conv)
        elif event.action == "update" and event.entity_id:
            conv = db.query(Conversation).filter(
                Conversation.id == event.entity_id,
                Conversation.user_id == user.id
            ).first()
            if conv:
                for key, value in event.changes.items():
                    if hasattr(conv, key):
                        setattr(conv, key, value)
    
    elif event.entity_type == "message":
        from ...models.conversation import Message
        if event.action == "create" and event.entity_id:  # entity_id is conversation_id
            msg = Message(
                conversation_id=event.entity_id,
                role=event.changes.get("role", "user"),
                content=event.changes.get("content", ""),
                tokens=event.changes.get("tokens", 0),
                metadata_json=event.changes.get("metadata", {})
            )
            db.add(msg)
            
            # Update conversation stats
            conv = db.query(Conversation).filter(Conversation.id == event.entity_id).first()
            if conv:
                conv.message_count += 1
                conv.total_tokens += msg.tokens
                conv.last_message_at = datetime.utcnow()
    
    db.commit()
    
    # Notifica outros clientes via WebSocket
    await manager.broadcast({
        "type": "sync",
        "entity": event.entity_type,
        "changes": event.changes,
        "user_id": user.id
    })
    
    return {"status": "synced", "timestamp": datetime.utcnow()}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket para atualizações em tempo real"""
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Processa mensagens em tempo real
            await manager.send_personal_message(data, user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
