import os
import aiohttp
import re
from typing import Dict, Any
from services.base_handler import BaseHandler

class WeatherHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.logger.info(f"WeatherHandler initialized with API key: {'Present' if self.api_key else 'Missing'}")

    async def handle(self, message: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Extract location from message or parameters
            location = self._extract_location(message, params)
            
            # Default to London if no location found
            location = location or 'London'
            
            self.logger.info(f"Weather requested for location: {location}")
            
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Weather API key not configured'
                }

            async with aiohttp.ClientSession() as session:
                self.logger.info(f"Making request to OpenWeather API for {location}")
                async with session.get(
                    self.base_url,
                    params={
                        'q': location,
                        'appid': self.api_key,
                        'units': 'metric'
                    }
                ) as response:
                    if response.status == 200:
                        weather_data = await response.json()
                        self.logger.info(f"Weather API response received successfully for {location}")
                        return {
                            'success': True,
                            'data': weather_data,
                            'location': location
                        }
                    else:
                        error_data = await response.text()
                        self.logger.error(f"Weather API error: {response.status} - {error_data}")
                        return {
                            'success': False,
                            'error': f"Weather API error: {response.status} - {error_data}"
                        }
        except Exception as e:
            self.logger.error(f"Weather handler error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_location(self, message: str, params: Dict[str, Any]) -> str:
        """Extract location from message or parameters"""
        location = None
        
        # Method 1: Try to get from AI parameters
        if isinstance(params.get('parameters'), dict):
            location = params['parameters'].get('location')
            
        # Method 2: Try to extract from AI response
        if not location and isinstance(params.get('ai_response'), str):
            response_lower = params['ai_response'].lower()
            if 'weather in ' in response_lower:
                location = response_lower.split('weather in ')[1].split()[0]
        
        # Method 3: Try to extract from the message using regex
        if not location:
            # Look for patterns like "weather in [location]" or "what's the weather in [location]"
            weather_pattern = re.compile(r'weather\s+(?:in|at|for)\s+([a-zA-Z\s]+)(?:\?|\.|\s|$)')
            match = weather_pattern.search(message.lower())
            if match:
                location = match.group(1).strip()
                
        return location

    def format_response(self, data: Dict[str, Any]) -> str:
        if not data.get('success'):
            return f"Sorry, I couldn't get the weather information: {data.get('error')}"
            
        weather_data = data['data']
        location = data.get('location') or weather_data['name']
        temp = weather_data['main']['temp']
        description = weather_data['weather'][0]['description']
        humidity = weather_data['main']['humidity']
        feels_like = weather_data['main']['feels_like']
        
        return (f"🌤️ Current weather in {weather_data['name']}:\n"
                f"Temperature: {temp}°C (feels like {feels_like}°C)\n"
                f"Conditions: {description}\n"
                f"Humidity: {humidity}%")
