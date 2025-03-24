import asyncio
import os
from services.handlers.movie_handler import MovieHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_movie_handler():
    print("Starting Movie Handler Airtable Integration Test...")
    
    # Create movie handler
    handler = MovieHandler()
    print(f"TMDB API Key: {bool(handler.api_key)}")
    print(f"Airtable API Key: {bool(handler.airtable_api_key)}")
    print(f"Airtable Base ID: {bool(handler.airtable_base_id)}")
    print(f"Airtable Movie Favorites Table: {handler.airtable_favorites_table}")
    print(f"Airtable Movies Watched Table: {handler.airtable_watched_table}")
    print(f"Airtable integration available: {handler.airtable_available}")
    print()
    
    if not handler.api_key:
        print("ERROR: TMDB API key is not set or invalid. Please add a valid key to your .env file:")
        print("TMDB_API_KEY=your_api_key")
        print("You can get a free API key at: https://www.themoviedb.org/settings/api")
        return
        
    if not handler.airtable_available:
        print("ERROR: Airtable integration is not available. Check the following:")
        print(f"1. Airtable API Key available: {bool(handler.airtable_api_key)}")
        print(f"2. Airtable Base ID available: {bool(handler.airtable_base_id)}")
        print(f"3. Make sure tables '{handler.airtable_favorites_table}' and '{handler.airtable_watched_table}' exist in your base")
        print(f"4. Make sure your API key has permissions to access the base: {handler.airtable_base_id}")
        print("Movies will not be tracked.")
    
    # Test connection to Airtable tables
    if handler.airtable_available:
        try:
            # Check if we can list records from the tables
            print("Testing connection to Airtable tables...")
            favorites = handler.favorites_table.all(max_records=1)
            print(f"- Successfully connected to {handler.airtable_favorites_table} table")
            watched = handler.watched_table.all(max_records=1)
            print(f"- Successfully connected to {handler.airtable_watched_table} table")
            print("Airtable connection test successful!")
        except Exception as e:
            print(f"ERROR: Failed to connect to Airtable tables: {e}")
            print("Please check your Airtable configuration and permissions.")
    
    print("\n--------------------------------------------------\n")
    
    # Test 1: Adding a movie to favorites
    print("--- Test 1: Adding a movie to favorites ---")
    result = await handler.handle('add "The Shawshank Redemption" to my favorites', {})
    print(f"Result: {result.get('success')}")
    print(f"Message: {result.get('message', '')}")
    print(f"Error: {result.get('error', '')}")
    print()
    
    # Test 2: Rating a movie
    print("--- Test 2: Rating a movie ---")
    result = await handler.handle('rate "Inception" 4.5/5', {})
    print(f"Result: {result.get('success')}")
    print(f"Message: {result.get('message', '')}")
    print(f"Error: {result.get('error', '')}")
    print()
    
    # Test 3: Recommending movies (personalized)
    print("--- Test 3: Getting personalized recommendations ---")
    result = await handler.handle("recommend movies", {})
    print(f"Result: {result.get('success')}")
    if result.get('success'):
        print(f"Category: {result.get('category', '')}")
        print(f"Found {result.get('count', 0)} recommendations")
        print("\nFormatted response:")
        print(handler.format_response(result))
    else:
        print(f"Error: {result.get('error', '')}")
    print()
    
    # Test 4: Recommending movies similar to another movie
    print("--- Test 4: Recommending similar movies ---")
    result = await handler.handle('recommend movies similar to "The Dark Knight"', {})
    print(f"Result: {result.get('success')}")
    if result.get('success'):
        print(f"Category: {result.get('category', '')}")
        print(f"Found {result.get('count', 0)} recommendations")
        print("\nFormatted response:")
        print(handler.format_response(result))
    else:
        print(f"Error: {result.get('error', '')}")

if __name__ == "__main__":
    asyncio.run(test_movie_handler()) 