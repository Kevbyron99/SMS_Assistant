import os
import asyncio
from dotenv import load_dotenv
from services.handlers.movie_handler import MovieHandler

# Load environment variables
load_dotenv()

async def test_movie():
    print("Starting Movie Handler test...")
    movie_handler = MovieHandler()
    
    # Get API key from environment
    api_key = os.getenv('TMDB_API_KEY')
    print(f"TMDB API Key available: {api_key is not None}")
    
    # Test different movie queries
    test_cases = [
        "what are some popular movies",
        "recommend me a comedy movie",
        "find movies like The Matrix",
        "search movie called Inception",
        "suggest a good action movie",
        "what are good science fiction movies",
        "recommend me something to watch"
    ]
    
    for case in test_cases:
        print(f"\n--- Testing query: '{case}' ---")
        result = await movie_handler.handle(case, {})
        
        print("Handler response:")
        print(f"Success: {result.get('success')}")
        
        if result.get('success'):
            if 'count' in result:
                print(f"Found {result.get('count')} movies")
                print(f"Category: {result.get('category')}")
                
            formatted = movie_handler.format_response(result)
            print("\nFormatted response:")
            print(formatted)
        else:
            print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_movie()) 