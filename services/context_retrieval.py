
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from services.airtable_service import AirtableService
from services.preference_learning import PreferenceLearning

logger = logging.getLogger(__name__)

class ContextRetrieval:
    def __init__(self):
        self.airtable = AirtableService()
        
    async def get_context(self, user_id: str, current_intent: str) -> Dict:
        """Get relevant context for the current conversation"""
        try:
            # Get recent conversations
            recent = await self._get_recent_history(user_id)
            
            # Get intent-specific history
            intent_history = await self._get_intent_history(user_id, current_intent)
            
            # Get user preferences
            preferences = await self._get_user_preferences(user_id)
            
            return {
                'recent_context': recent,
                'intent_context': intent_history,
                'user_preferences': preferences
            }
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {}
            
    async def _get_recent_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent conversation history"""
        return await self.airtable.get_recent_conversations(user_id, limit)
        
    async def _get_intent_history(self, user_id: str, intent: str) -> List[Dict]:
        """Get history specific to current intent"""
        return await self.airtable.get_conversations_by_intent(user_id, intent)
        
    async def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences using PreferenceLearning system"""
        try:
            preference_learner = PreferenceLearning()
            preferences = await preference_learner.learn_preferences(user_id)
            return preferences
        except Exception as e:
            logger.error(f"Error extracting preferences: {e}")
            return {}
