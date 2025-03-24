import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_tmdb_api():
    """Test if the TMDB API key is working"""
    print("Testing TMDB API Connection...")
    
    # Get the API key from environment
    api_key = os.getenv('TMDB_API_KEY')
    
    if not api_key:
        print("ERROR: TMDB API key not found in .env file")
        return False
        
    print(f"TMDB API Key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")
    
    # Test the API by fetching popular movies
    url = f"https://api.themoviedb.org/3/movie/popular"
    params = {
        'api_key': api_key,
        'language': 'en-US',
        'page': 1
    }
    
    try:
        print("\nFetching popular movies from TMDB API...")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            movies = data.get('results', [])[:5]  # Get top 5 movies
            
            print(f"Successfully fetched {len(movies)} popular movies:")
            for i, movie in enumerate(movies, 1):
                title = movie.get('title', 'Unknown')
                year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A'
                rating = movie.get('vote_average', 0)
                print(f"{i}. {title} ({year}) - {rating}/10")
                
            # Test movie details endpoint
            if movies:
                movie_id = movies[0]['id']
                print(f"\nFetching details for movie ID: {movie_id}...")
                
                details_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
                details_response = requests.get(details_url, params=params)
                
                if details_response.status_code == 200:
                    details = details_response.json()
                    print(f"Title: {details.get('title')}")
                    print(f"Runtime: {details.get('runtime')} minutes")
                    print(f"Genres: {', '.join([g['name'] for g in details.get('genres', [])])}")
                    
                    # Get director information
                    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
                    credits_response = requests.get(credits_url, params=params)
                    
                    if credits_response.status_code == 200:
                        credits = credits_response.json()
                        directors = [member['name'] for member in credits.get('crew', []) 
                                    if member.get('job') == 'Director']
                        
                        if directors:
                            print(f"Director(s): {', '.join(directors)}")
                    else:
                        print(f"Error fetching credits: {credits_response.status_code} - {credits_response.text}")
                else:
                    print(f"Error fetching movie details: {details_response.status_code} - {details_response.text}")
            
            return True
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error connecting to TMDB API: {e}")
        return False

if __name__ == "__main__":
    test_tmdb_api() 