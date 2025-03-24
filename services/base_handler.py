import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseHandler(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def handle(self, message: str, params: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def format_response(self, data: Dict[str, Any]) -> str:
        return str(data)
