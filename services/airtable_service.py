
import os
import logging
from datetime import datetime
from airtable import Airtable
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AirtableService:
    def __init__(self):
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.table_name = 'Conversations'
        
        logger.info(f"Base ID format check: {'app' in str(self.base_id) if self.base_id else 'missing'}")
        logger.info(f"API Key format check: {'pat' in str(self.api_key).lower() if self.api_key else 'missing'}")
        
        if not self.base_id or not self.api_key:
            logger.warning("Airtable credentials not found - storage disabled")
            self.airtable = None
        else:
            if not str(self.base_id).startswith('app'):
                logger.error("Invalid base_id format - Should start with 'app'")
                self.airtable = None
                return
            if not str(self.api_key).lower().startswith('pat'):
                logger.error("Invalid api_key format - Should start with 'pat'")
                self.airtable = None
                return
            try:
                self.airtable = Airtable(self.base_id, self.table_name, self.api_key)
                logger.info("Airtable connection successful")
            except Exception as e:
                logger.error(f"Airtable connection failed: {str(e)}")
                self.airtable = None

    def store_conversation(self, user_id: str, message: str, response: str) -> Dict:
        """Store a conversation entry in Airtable"""
        if not self.airtable:
            logger.info("Airtable storage disabled - skipping")
            return {"status": "storage_disabled"}
        try:
            fields = {
                'From': user_id,        # Mobile number
                'Body': message,        # Long Text
                'Response': response,   # Long Text
                'Intent': ''           # Single line text
            }
            return self.airtable.insert(fields)
        except Exception as e:
            logger.error(f"Error storing conversation in Airtable: {e}")
            return {"error": str(e)}

    def get_user_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Retrieve conversation history for a user"""
        formula = f"{{From}} = '{user_id}'"
        return self.airtable.get_all(formula=formula, max_records=limit)

    async def get_recent_conversations(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent conversations for a user"""
        if not self.airtable:
            return []
        try:
            return self.get_user_history(user_id, limit)
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            return []

    async def get_conversations_by_intent(self, user_id: str, intent: str) -> List[Dict]:
        """Get conversations filtered by intent"""
        if not self.airtable:
            return []
        try:
            formula = f"AND({{From}} = '{user_id}', {{Intent}} = '{intent}')"
            return self.airtable.get_all(formula=formula, max_records=5)
        except Exception as e:
            logger.error(f"Error getting intent conversations: {e}")
            return []

    async def get_all_user_conversations(self, user_id: str) -> List[Dict]:
        """Get all conversations for a user"""
        if not self.airtable:
            return []
        try:
            formula = f"{{From}} = '{user_id}'"
            return self.airtable.get_all(formula=formula)
        except Exception as e:
            logger.error(f"Error getting all conversations: {e}")
            return []
