import asyncio
import os
import json
from services.handlers.movie_handler import MovieHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_movie_recommendations():
    print("Testing Movie Recommendations with TMDB API...")
    
    # Create movie handler
    handler = MovieHandler()
    print(f"TMDB API Key: {bool(handler.api_key)}")
    print(f"Airtable integration available: {handler.airtable_available}")
    print(f"Watched Table available: {handler.watched_table_available}")
    print(f"Favorites Table available: {handler.favorites_table_available}")
    
    # Test 1: Get Popular Movies
    print("\n--- Test 1: Get Popular Movies ---")
    result = await handler.handle("recommend popular movies", {})
    
    print("Text Response:")
    print(result.get('text', 'No text response'))
    
    # Pretty print the structured data
    print("\nStructured Data for Assistant:")
    structured_data = result.get('data', {})
    print(f"Type: {structured_data.get('type')}")
    print(f"Success: {structured_data.get('success')}")
    print(f"Category: {structured_data.get('category')}")
    print(f"Count: {structured_data.get('count')}")
    
    # Print a sample of the first movie if available
    movies = structured_data.get('movies', [])
    if movies:
        print("\nFirst Movie Sample:")
        first_movie = movies[0]
        print(f"Title: {first_movie.get('title')}")
        print(f"Year: {first_movie.get('year')}")
        print(f"Rating: {first_movie.get('rating')}")
        print(f"Genres: {', '.join(first_movie.get('genres', []))}")
        if 'poster_url' in first_movie:
            print(f"Poster URL: {first_movie.get('poster_url')}")
    
    # Test 2: Get Movies by Genre
    print("\n--- Test 2: Get Movies by Genre (Action) ---")
    result = await handler.handle("recommend action movies", {})
    
    print("Text Response:")
    print(result.get('text', 'No text response'))
    
    # Test 3: Search Movies
    print("\n--- Test 3: Search for Movies ---")
    result = await handler.handle("find movie called Inception", {})
    
    print("Text Response:")
    print(result.get('text', 'No text response'))
    
    # Test 4: Get Similar Movies
    print("\n--- Test 4: Get Similar Movies ---")
    result = await handler.handle("recommend movies similar to The Dark Knight", {})
    
    print("Text Response:")
    print(result.get('text', 'No text response'))
    
    # Test 5: Rate a Movie (this will add to watched)
    if handler.airtable_available and handler.watched_table_available:
        print("\n--- Test 5: Rate a Movie ---")
        result = await handler.handle('rate "The Shawshank Redemption" 4.5/5', {})
        
        print("Text Response:")
        print(result.get('text', 'No text response'))
        print("\nStructured Data for Assistant:")
        structured_data = result.get('data', {})
        if 'message' in structured_data:
            print(f"Message: {structured_data.get('message', '')}")
    
    # Test 6: Get Personalized Recommendations
    print("\n--- Test 6: Get Personalized Recommendations ---")
    result = await handler.handle("recommend movies for me", {})
    
    print("Text Response:")
    print(result.get('text', 'No text response'))
    
    # Save a sample response to a JSON file for reference
    try:
        with open('movie_recommendation_sample.json', 'w') as f:
            sample_data = result.get('data', {})
            json.dump(sample_data, f, indent=2)
            print("\nSaved sample structured data to movie_recommendation_sample.json")
    except Exception as e:
        print(f"Error saving sample data: {e}")

if __name__ == "__main__":
    asyncio.run(test_movie_recommendations()) 