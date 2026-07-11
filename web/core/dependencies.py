from web.services.websocket_manager import WebSocketManager
from web.services.model_manager import ModelManager
from web.services.file_service import FileService
from web.services.audio_processing_service import AudioProcessingService

ws_manager = WebSocketManager()
model_manager = ModelManager()
file_service = FileService()
audio_service = AudioProcessingService(file_service, model_manager, ws_manager)

def get_ws_manager() -> WebSocketManager:
    return ws_manager

def get_model_manager() -> ModelManager:
    return model_manager

def get_file_service() -> FileService:
    return file_service

def get_audio_service() -> AudioProcessingService:
    return audio_service
