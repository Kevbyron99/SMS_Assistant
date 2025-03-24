import asyncio
import os
from services.handlers.shift_handler import ShiftHandler

async def test_shift_handler():
    print("Starting Enhanced Shift Handler Airtable Integration Test...")
    
    # Check if Airtable integration is available
    handler = ShiftHandler()
    print(f"Airtable API Key: {bool(handler.airtable_api_key)}")
    print(f"Airtable Base ID: {bool(handler.airtable_base_id)}")
    print(f"Airtable Shifts Table: {handler.airtable_table_name}")
    print(f"Airtable integration available: {handler.airtable_available}")
    print()
    
    if not handler.airtable_available:
        print("Airtable integration is not available. Test will use simulated data.")
    
    # Test 1: Adding a regular shift
    print("--- Adding a regular shift ---")
    result = await handler.handle("add shift on Monday from 9am to 5pm", {})
    print(f"Handler response: {result.get('message', '')}")
    print()
    
    # Test 2: Adding an overnight shift
    print("--- Adding an overnight shift ---")
    result = await handler.handle("add shift on Tuesday 10pm to Wednesday 10am", {})
    print(f"Handler response: {result.get('message', '')}")
    print()
    
    # Test 3: Adding a day off
    print("--- Marking a day off ---")
    result = await handler.handle("mark Friday as day off", {})
    print(f"Handler response: {result.get('message', '')}")
    print()
    
    # Test 4: Adding a shift with notes
    print("--- Adding a shift with notes ---")
    result = await handler.handle("add shift on Saturday from 12pm to 8pm notes: Special event coverage", {})
    print(f"Handler response: {result.get('message', '')}")
    print()
    
    # Test 5: Listing all shifts
    print("--- Testing: 'list all shifts' ---")
    result = await handler.handle("list all shifts", {})
    print(f"Handler response:")
    print(f"Success: {result.get('success')}")
    print(f"Found {result.get('count', 0)} shifts")
    print()
    print(f"Formatted response:")
    print(handler.format_response(result))
    print()
    
    # Test 6: Getting the next shift
    print("--- Testing: 'next shift' ---")
    result = await handler.handle("next shift", {})
    print(f"Handler response:")
    print(f"Success: {result.get('success')}")
    if result.get('shift'):
        print(f"Found upcoming shift")
    else:
        print(f"Message: {result.get('message', 'No shifts found')}")
    print()
    print(f"Formatted response:")
    print(handler.format_response(result))
    print()

if __name__ == "__main__":
    asyncio.run(test_shift_handler()) 