import asyncio
import os
import logging
from services.handlers.shift_handler import ShiftHandler
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_shifts")

# Load environment variables
load_dotenv()

async def test_special_shifts():
    print("Testing Special Shift Types (24-hour shifts and days off)...")
    
    # Create shift handler
    handler = ShiftHandler()
    print(f"Airtable API Key: {bool(handler.airtable_api_key)}")
    print(f"Airtable Base ID: {bool(handler.airtable_base_id)}")
    print(f"Airtable Shifts Table: {handler.airtable_table_name}")
    print(f"Airtable integration available: {handler.airtable_available}")
    print()
    
    if not handler.airtable_available:
        print("ERROR: Airtable integration is not available. Please check your .env file.")
        return
    
    # Test 1: Adding a 24-hour shift
    print("--- Test 1: Adding a 24-hour shift ---")
    logger.info("Testing a 24-hour shift command: add shift on Monday 10pm to Tuesday 10am")
    
    # Test with an explicit format to make sure the regex works
    result = await handler.handle("add shift from Monday 10pm to Tuesday 10am", {})
    
    print(f"Result: {result.get('success')}")
    print(f"Message: {result.get('message', '')}")
    print(f"Error: {result.get('error', '')}")
    print()
    
    # Test 2: Adding a day off
    print("--- Test 2: Marking a day off ---")
    result = await handler.handle("mark Wednesday as day off", {})
    print(f"Result: {result.get('success')}")
    print(f"Message: {result.get('message', '')}")
    print()
    
    # Test 3: List all shifts to see the new entries
    print("--- Test 3: Listing all shifts including special types ---")
    result = await handler.handle("list all shifts", {})
    print(f"Result: {result.get('success')}")
    print(f"Found: {result.get('count', 0)} shifts")
    print("\nFormatted response:")
    print(handler.format_response(result))
    print()
    
    # Test 4: Get next shift
    print("--- Test 4: Getting next shift ---")
    result = await handler.handle("next shift", {})
    print(f"Result: {result.get('success')}")
    if 'message' in result:
        print(f"Message: {result.get('message')}")
    elif 'shift' in result:
        print(f"Found next shift: {result['shift'].get('date')} {result['shift'].get('start_time')}-{result['shift'].get('end_time')}")
        print(f"Status: {result['shift'].get('status')}")
        print(f"Notes: {result['shift'].get('notes', '')}")
    print("\nFormatted response:")
    print(handler.format_response(result))

if __name__ == "__main__":
    asyncio.run(test_special_shifts()) 