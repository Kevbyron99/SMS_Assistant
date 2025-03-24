import asyncio
from services.handlers.transport_handler import TransportHandler
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_transport():
    # Load environment variables
    load_dotenv()
    
    # Force simulation mode off
    os.environ['TRANSPORT_SIMULATION'] = 'false'
    
    # Initialize the transport handler
    handler = TransportHandler()
    
    # Print configuration
    logger.info(f"API Key: {'Present' if handler.api_key else 'Missing'}")
    logger.info(f"App ID: {handler.app_id}")
    logger.info(f"Simulation Mode: {handler.simulation_mode}")
    
    # Test cases
    test_cases = [
        "When's the next train from Urmston to Manchester?",
        "Trains from Manchester to Liverpool",
        "Show me trains from London Euston to Manchester",
        "Next train from Manchester to Leeds"
    ]
    
    print("\nTesting Transport Service...")
    print("-" * 50)
    
    for test_message in test_cases:
        print(f"\nTesting message: {test_message}")
        try:
            # Call the handler
            result = await handler.handle(test_message, {})
            
            # Print raw result for debugging
            logger.info(f"Raw API result: {result}")
            
            # Format and print the response
            if result.get('success'):
                formatted_response = handler.format_response(result)
                print("Response:", formatted_response)
            else:
                print("Error:", result.get('error'))
                
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            logger.exception("Detailed error:")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_transport()) 