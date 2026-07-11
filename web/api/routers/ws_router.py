from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from web.core.dependencies import get_ws_manager
from web.services.websocket_manager import WebSocketManager

router = APIRouter(prefix="/api/v1/ws", tags=["WebSocket"])

@router.websocket("/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str,
    ws_manager: WebSocketManager = Depends(get_ws_manager)
):
    await ws_manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
