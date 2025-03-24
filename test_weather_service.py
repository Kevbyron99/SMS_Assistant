import asyncio
from services.handlers.weather_handler import WeatherHandler
import os
from dotenv import load_dotenv

async def test_weather():
    # Load environment variables
    load_dotenv()
    
    # Initialize the weather handler
    handler = WeatherHandler()
    
    # Test cases
    test_cases = [
        "What's the weather in London?",
        "Weather in New York",
        "Tell me the weather in Tokyo"
    ]
    
    print("Testing Weather Service...")
    print("-" * 50)
    
    for test_message in test_cases:
        print(f"\nTesting message: {test_message}")
        try:
            # Call the handler
            result = await handler.handle(test_message, {})
            
            # Format and print the response
            if result.get('success'):
                formatted_response = handler.format_response(result)
                print("Response:", formatted_response)
            else:
                print("Error:", result.get('error'))
                
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_weather()) 