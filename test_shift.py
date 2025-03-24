import os
import asyncio
from dotenv import load_dotenv
from services.handlers.shift_handler import ShiftHandler

# Load environment variables
load_dotenv()

async def test_shift():
    print("Starting Shift Handler test...")
    shift_handler = ShiftHandler()
    
    # Test different shift queries
    test_cases = [
        "next shift",
        "list all shifts",
        "list shifts for today",
        "list shifts for tomorrow",
        "list shifts this week",
        "list shifts next week",
        "add shift on Monday at 9am",
        "delete shift tomorrow"
    ]
    
    for case in test_cases:
        print(f"\n--- Testing query: '{case}' ---")
        result = await shift_handler.handle(case, {})
        
        print("Handler response:")
        print(f"Success: {result.get('success')}")
        
        if result.get('success'):
            if 'count' in result:
                print(f"Found {result.get('count')} shifts")
                
            formatted = shift_handler.format_response(result)
            print("\nFormatted response:")
            print(formatted)
        else:
            print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_shift()) 