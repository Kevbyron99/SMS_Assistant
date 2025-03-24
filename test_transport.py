import asyncio
import json
import logging
import os
import requests
from dotenv import load_dotenv
from services.handlers.transport_handler import TransportHandler

# Configure logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

async def test_transport():
    print("Starting Transport API test...")
    
    # Check if the API key is available
    transport_api_key = os.getenv('TRANSPORT_API_KEY')
    transport_app_id = os.getenv('TRANSPORT_APP_ID')
    print(f"Transport API Key available: {bool(transport_api_key)}")
    print(f"Transport API Key: {transport_api_key}")
    print(f"App ID: {transport_app_id}")
    
    # Test direct URL with query parameters directly in the URL
    print("\n--- Testing direct URL with query parameters ---")
    direct_url = f"https://transportapi.com/v3/uk/places.json?app_id={transport_app_id}&app_key={transport_api_key}&query=Urmston&type=train_station"
    print(f"Direct URL: {direct_url}")
    
    try:
        response = requests.get(direct_url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test message
    test_message = "next train from urmston to manchester oxford road"
    print(f"\nTest message: '{test_message}'")
    
    # Initialize the handler
    handler = TransportHandler()
    
    # Now try via the handler
    print("\n--- Testing via the transport handler ---")
    result = await handler.handle(test_message, {})
    
    # Print the raw response
    print("\nHandler API Response:")
    print(json.dumps(result, indent=2))
    
    # Print the formatted response
    print("\nFormatted Response:")
    print(handler.format_response(result))

if __name__ == "__main__":
    asyncio.run(test_transport()) 