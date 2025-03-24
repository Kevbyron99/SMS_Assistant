import asyncio
import os
from services.handlers.movie_handler import MovieHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_movie_handler():
    print("Starting Simple Movie Handler Test...")
    
    # Create movie handler
    handler = MovieHandler()
    print(f"TMDB API Key: {bool(handler.api_key)}")
    print(f"Airtable API Key: {bool(handler.airtable_api_key)}")
    print(f"Airtable Base ID: {bool(handler.airtable_base_id)}")
    print(f"Airtable Movie Favorites Table: {handler.airtable_favorites_table}")
    print(f"Airtable Movies Watched Table: {handler.airtable_watched_table}")
    print(f"Airtable integration available: {handler.airtable_available}")
    print(f"Watched Table available: {handler.watched_table_available}")
    print(f"Favorites Table available: {handler.favorites_table_available}")
    print()
    
    # Test adding a movie to watched by direct Airtable access
    if handler.airtable_available and handler.watched_table_available:
        print("Testing direct addition to Movies Watched table...")
        try:
            current_date = '2025-03-23'  # Use a fixed date for testing
            new_movie = {
                'Title': "Test Movie Direct",
                'Date Watched': current_date,
                'User Rating': 4.0
            }
            
            try:
                record = handler.watched_table.create(new_movie)
                print(f"Successfully added movie with fields: {new_movie}")
                print(f"Record ID: {record['id']}")
            except Exception as e:
                print(f"Error with standard fields: {e}")
                
                # Try alternative field names
                if "Unknown field name" in str(e):
                    alt_movie = {
                        'Name': "Test Movie Direct (Alt)",
                        'Date': current_date,
                        'Rating': 4.0
                    }
                    
                    record = handler.watched_table.create(alt_movie)
                    print(f"Successfully added movie with alternative fields: {alt_movie}")
                    print(f"Record ID: {record['id']}")
        except Exception as e:
            print(f"Error adding movie directly: {e}")
    
    # Test format_response with a simulated result
    print("\nTesting format_response with simulated data...")
    mock_data = {
        'success': True,
        'movies': [
            {
                'title': 'Test Movie 1',
                'release_date': '2023-05-15',
                'vote_average': 8.5,
                'genre_ids': [28, 12, 878],  # Action, Adventure, Sci-Fi
                'overview': 'This is a test movie with a long description that should be truncated if it exceeds the character limit set in the format_response method.'
            },
            {
                'title': 'Test Movie 2',
                'release_date': '2024-01-30',
                'vote_average': 7.2,
                'genre_ids': [18, 10749],  # Drama, Romance
                'overview': 'Another test movie with a shorter description.'
            }
        ],
        'count': 2,
        'category': 'Test Movies'
    }
    
    formatted = handler.format_response(mock_data)
    print(formatted)
    
if __name__ == "__main__":
    asyncio.run(test_movie_handler()) 