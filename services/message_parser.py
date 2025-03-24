import openai
import os
import logging
import asyncio
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageParser:
    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_key:
            logger.error("OpenAI API key is missing!")
            raise ValueError("OpenAI API key is required")
        openai.api_key = self.openai_key

        self.assistant_id = os.getenv('OPENAI_ASSISTANT_ID')
        if not self.assistant_id:
            logger.error("OpenAI Assistant ID is missing!")
            raise ValueError("OpenAI Assistant ID is required")

    def _get_initial_intent(self, message: str) -> str:
        """Get initial intent classification for better context retrieval"""
        message = message.lower()
        if any(word in message for word in ['weather', 'temperature', 'forecast']):
            return 'weather'
        elif any(word in message for word in ['movie', 'film', 'watch']):
            return 'movies'
        elif any(word in message for word in ['email', 'mail', 'inbox']):
            return 'email'
        elif any(word in message for word in ['bus', 'train', 'transport']):
            return 'transport'
        elif any(word in message for word in ['shift', 'schedule', 'work']):
            return 'shifts'
        return 'general'

    async def parse_message(self, message: str, user_id: str = "default") -> Dict:
        """Parse incoming message to determine intent and parameters"""
        from services.context_retrieval import ContextRetrieval

        try:
            # Get context for the conversation
            context_service = ContextRetrieval()

            # Get initial intent and handle API calls first
            initial_intent = self._get_initial_intent(message)

            # If it's a transport request, get the data first
            api_response = None
            if initial_intent == 'transport':
                transport_handler = self._handle_transport
                api_response = await transport_handler(message, {})

            # Use OpenAI Assistant
            thread = openai.beta.threads.create()

            # Get context
            context = await context_service.get_context(user_id, initial_intent)

            # Add message with context to thread
            context_prompt = f"""
Context:
- Recent interactions: {context['recent_context']}
- Related history: {context['intent_context']}
- User preferences: {context['user_preferences']}

User message: {message}

API Response: {api_response if api_response else 'No API data available'}
"""
            openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=context_prompt
            )

            # Run the assistant
            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=os.getenv('OPENAI_ASSISTANT_ID')
            )

            # Wait for completion
            while run.status not in ['completed', 'failed']:
                run = openai.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                if run.status == 'failed':
                    raise Exception("Assistant run failed")

            # Wait for completion with timeout
            max_retries = 10
            retry_count = 0
            while run.status not in ['completed', 'failed']:
                if retry_count >= max_retries:
                    raise Exception("Assistant response timeout")
                run = openai.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                retry_count += 1
                await asyncio.sleep(1)

            if run.status == 'failed':
                raise Exception("Assistant run failed")

            # Get the assistant's response
            messages = openai.beta.threads.messages.list(thread_id=thread.id)
            if not messages.data:
                raise Exception("No response received from assistant")

            ai_response = messages.data[0].content[0].text.value

            # Parse AI response for intent classification
            intent = self._get_initial_intent(message)  # Use message intent
            parameters = {'ai_response': ai_response, 'original_message': message}

            # Basic intent mapping
            intents = {
                'weather': self._handle_weather,
                'movies': self._handle_movies,
                'email': self._handle_email,
                'transport': self._handle_transport,
                'shifts': self._handle_shifts
            }

            # Default to general conversation if no specific intent matched
            handler = intents.get(intent, self._handle_general)
            if intent in ['weather', 'transport']:
                return await handler(message, parameters)
            return handler(message, parameters)
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {e}")
            return self._handle_general(message, {'message': message})

    async def _handle_weather(self, message: str, params: Dict) -> Dict:
        from services.handlers.weather_handler import WeatherHandler
        handler = WeatherHandler()
        result = await handler.handle(message, params)
        response = handler.format_response(result)
        return {'intent': 'weather', 'parameters': response}

    def _handle_movies(self, message: str, params: Dict) -> Dict:
        return {'intent': 'movies', 'parameters': params}

    def _handle_email(self, message: str, params: Dict) -> Dict:
        return {'intent': 'email', 'parameters': params}

    async def _handle_transport(self, message: str, params: Dict) -> Dict:
        # Uncomment the transport handler code
        from services.handlers.transport_handler import TransportHandler
        handler = TransportHandler()
        result = await handler.handle(message, params)
        return {'intent': 'transport', 'parameters': result}

    def _handle_shifts(self, message: str, params: Dict) -> Dict:
        return {'intent': 'shifts', 'parameters': params}

    def _handle_general(self, message: str, params: Dict) -> Dict:
        return {'intent': 'conversation', 'parameters': params.get('ai_response', message)}