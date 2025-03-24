
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseHandler:
    def __init__(self):
        self.logger = logger

    async def handle(self, message: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Base handle method to be implemented by specific handlers"""
        raise NotImplementedError("Handler must implement handle method")

    def format_response(self, data: Dict[str, Any]) -> str:
        """Format handler response for messaging"""
        raise NotImplementedError("Handler must implement format_response method")
