
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from services.airtable_service import AirtableService

logger = logging.getLogger(__name__)

class PreferenceLearning:
    def __init__(self):
        self.airtable = AirtableService()
        
    async def learn_preferences(self, user_id: str) -> Dict:
        """Learn user preferences from historical data"""
        try:
            history = await self.airtable.get_all_user_conversations(user_id)
            preferences = {
                'services': await self._analyze_service_usage(history),
                'timing': await self._analyze_timing_patterns(history),
                'locations': await self._analyze_locations(history),
                'topics': await self._analyze_topics(history)
            }
            await self._store_preferences(user_id, preferences)
            return preferences
        except Exception as e:
            logger.error(f"Error learning preferences: {e}")
            return {}
            
    async def _analyze_service_usage(self, history: List[Dict]) -> Dict:
        """Analyze which services the user uses most frequently"""
        service_counts = {}
        for interaction in history:
            if 'intent' in interaction:
                service = interaction['intent']
                service_counts[service] = service_counts.get(service, 0) + 1
        return {'most_used': sorted(service_counts.items(), key=lambda x: x[1], reverse=True)}
        
    async def _analyze_timing_patterns(self, history: List[Dict]) -> Dict:
        """Analyze when the user is most active"""
        hour_counts = {i: 0 for i in range(24)}
        for interaction in history:
            if 'timestamp' in interaction:
                hour = datetime.fromisoformat(interaction['timestamp']).hour
                hour_counts[hour] += 1
        return {'peak_hours': sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]}
        
    async def _analyze_locations(self, history: List[Dict]) -> List[str]:
        """Extract frequently referenced locations"""
        locations = set()
        for interaction in history:
            if 'parameters' in interaction and 'location' in interaction['parameters']:
                locations.add(interaction['parameters']['location'])
        return list(locations)
        
    async def _analyze_topics(self, history: List[Dict]) -> Dict:
        """Analyze frequently discussed topics"""
        topic_counts = {}
        for interaction in history:
            if 'topics' in interaction:
                for topic in interaction['topics']:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
        return {'frequent_topics': sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)}
        
    async def _store_preferences(self, user_id: str, preferences: Dict) -> None:
        """Store learned preferences in Airtable"""
        try:
            await self.airtable.update_user_preferences(user_id, preferences)
        except Exception as e:
            logger.error(f"Error storing preferences: {e}")
