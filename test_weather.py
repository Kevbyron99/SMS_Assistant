import os
import asyncio
from dotenv import load_dotenv
from services.handlers.weather_handler import WeatherHandler

# Load environment variables
load_dotenv()

async def test_weather():
    print("Starting Weather API test...")
    weather_handler = WeatherHandler()
    
    # Get API key from environment
    api_key = os.getenv('OPENWEATHER_API_KEY')
    print(f"Weather API Key available: {api_key is not None}")
    
    # Test different locations
    locations = ["London", "Manchester", "New York", "Tokyo"]
    
    for location in locations:
        print(f"\n--- Testing weather for {location} ---")
        message = f"What's the weather in {location}?"
        result = await weather_handler.handle(message, {})
        
        if result['success']:
            print("API Response Success!")
            print(weather_handler.format_response(result))
        else:
            print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_weather()) 