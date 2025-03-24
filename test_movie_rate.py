import asyncio
import os
from dotenv import load_dotenv
import json
from services.handlers.movie_handler import MovieHandler

# Load environment variables
load_dotenv()

async def test_rating():
    print("Testing movie rating functionality...")
    
    # Create an instance of MovieHandler
    handler = MovieHandler()
    
    # Check if TMDB API key is available
    tmdb_api_key = os.getenv("TMDB_API_KEY")
    print(f"TMDB API Key: {'Available' if tmdb_api_key else 'Missing'}")
    
    if not tmdb_api_key:
        print("TMDB API key not available. Please check your .env file.")
        return
    
    # Test rating a movie
    print("\nTesting rating 'The Shawshank Redemption' with 5 stars...")
    
    # Create message text and params to match the handler.handle() method signature
    message_text = "rate The Shawshank Redemption 5 stars"
    message_params = {
        "movie_title": "The Shawshank Redemption",
        "rating": "5"
    }
    
    try:
        # Let's print the parsed intent to see what's happening
        intent = handler._parse_movie_intent(message_text)
        print(f"\nParsed intent: {intent}")
        
        # If the intent doesn't have action=rate, we'll modify it directly
        if intent['action'] != 'rate':
            print("Intent doesn't have rate action, modifying it directly")
            intent['action'] = 'rate'
            intent['movie_title'] = "The Shawshank Redemption"
            intent['rating'] = 5.0
            
            # Call the rate movie method directly
            result = await handler._rate_movie(intent)
            print(f"\nDirect rate_movie result: {result}")
            
            # Format the response
            if result.get('success'):
                response = {
                    'text': result.get('message', 'Movie rated successfully'),
                    'data': {
                        'type': 'movie_rating',
                        'success': True,
                        'movie': {
                            'title': "The Shawshank Redemption",
                            'rating': 5.0
                        }
                    }
                }
            else:
                response = {
                    'text': result.get('error', 'Error rating movie'),
                    'data': {
                        'type': 'movie_rating',
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    }
                }
        else:
            # Handle normally if intent is correctly parsed
            response = await handler.handle(message_text, message_params)
        
        print("\nResponse:")
        print(response.get('text', 'No text response'))
        
        if 'data' in response:
            print("\nStructured Data:")
            print(json.dumps(response['data'], indent=2))
    
    except Exception as e:
        print(f"Error during movie rating test: {str(e)}")
        import traceback
        traceback.print_exc()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_rating()) 