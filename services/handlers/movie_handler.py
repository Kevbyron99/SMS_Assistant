import os
import re
from typing import Dict, Any, List, Optional
import aiohttp
import json
import random
from services.base_handler import BaseHandler
from datetime import datetime

class MovieHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('TMDB_API_KEY')
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        self.logger.info(f"MovieHandler initialized with API key available: {self.api_key is not None}")
        
        # Airtable setup for movie tracking
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
        self.airtable_favorites_table = os.getenv('AIRTABLE_MOVIE_FAVORITES', 'Movie Favorites')
        self.airtable_watched_table = os.getenv('AIRTABLE_MOVIES_WATCHED', 'Movies Watched')
        
        # Set up Airtable connection
        try:
            from pyairtable import Api
            if self.airtable_api_key and self.airtable_base_id:
                self.airtable_api = Api(self.airtable_api_key)
                self.airtable_base = self.airtable_api.base(self.airtable_base_id)
                
                # Check if we can access the watched table
                self.watched_table = self.airtable_base.table(self.airtable_watched_table)
                self.watched_table_available = True
                self.logger.info(f"Successfully connected to {self.airtable_watched_table} table")
                
                # Try to access favorites table, but continue if not available
                try:
                    self.favorites_table = self.airtable_base.table(self.airtable_favorites_table)
                    # Test if we can actually access the table
                    self.favorites_table.all(max_records=1)
                    self.favorites_table_available = True
                    self.logger.info(f"Successfully connected to {self.airtable_favorites_table} table")
                except Exception as e:
                    self.favorites_table_available = False
                    self.logger.warning(f"Could not access {self.airtable_favorites_table} table: {e}")
                
                self.airtable_available = self.watched_table_available
                self.logger.info(f"Movie handler initialized with Airtable integration (Watched: {self.watched_table_available}, Favorites: {self.favorites_table_available})")
            else:
                self.airtable_available = False
                self.watched_table_available = False
                self.favorites_table_available = False
                self.logger.warning("Airtable integration not available - missing API key or base ID")
        except Exception as e:
            self.logger.warning(f"Airtable integration not available: {e}")
            self.airtable_available = False
            self.watched_table_available = False
            self.favorites_table_available = False
        
        # Common genres for reference
        self.genres = {
            28: "Action",
            12: "Adventure",
            16: "Animation",
            35: "Comedy",
            80: "Crime",
            99: "Documentary",
            18: "Drama",
            10751: "Family",
            14: "Fantasy",
            36: "History",
            27: "Horror",
            10402: "Music",
            9648: "Mystery",
            10749: "Romance",
            878: "Science Fiction",
            10770: "TV Movie",
            53: "Thriller",
            10752: "War",
            37: "Western"
        }
        
        # Mapping from user-friendly genre names to IDs
        self.genre_mapping = {genre.lower(): id for id, genre in self.genres.items()}

    async def handle(self, message: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Extract movie query intent
            intent = self._parse_movie_intent(message.lower())
            self.logger.info(f"Parsed movie intent: {intent}")
            
            if not self.api_key:
                response = {
                    'success': False,
                    'error': 'Movie recommendations not available - TMDB API key not configured'
                }
                return {
                    'text': self.format_response(response),
                    'data': self.prepare_movie_data_for_assistant(response)
                }
            
            result = None
            if intent['action'] == 'popular':
                result = await self._get_popular_movies()
            elif intent['action'] == 'genre':
                result = await self._get_movies_by_genre(intent['genre'])
            elif intent['action'] == 'search':
                result = await self._search_movies(intent['query'])
            elif intent['action'] == 'recommend':
                result = await self._get_recommendations(intent)
            elif intent['action'] == 'add_favorite':
                result = await self._add_to_favorites(intent)
            elif intent['action'] == 'rate':
                result = await self._rate_movie(intent)
            else:
                # Default to popular movies
                result = await self._get_popular_movies()
            
            # Format the response for display and prepare structured data for the assistant
            return {
                'text': self.format_response(result),
                'data': self.prepare_movie_data_for_assistant(result)
            }
                
        except Exception as e:
            self.logger.error(f"Movie handler error: {str(e)}")
            error_result = {
                'success': False,
                'error': f"Error processing movie request: {str(e)}"
            }
            return {
                'text': self.format_response(error_result),
                'data': self.prepare_movie_data_for_assistant(error_result)
            }
    
    def _parse_movie_intent(self, message: str) -> Dict[str, Any]:
        """Parse the intent from the movie-related message"""
        intent = {'action': None, 'genre': None, 'query': None, 'release_year': None}
        
        # Check for rating a movie - add this check earlier in the function to give it priority
        rating_match = re.search(r'rate\s+(?:the\s+)?(?:movie\s+)?["\']?([^"\']+)["\']?(?:\s+as\s+)?(\d+(?:\.\d+)?)(?:\s+stars?)?(?:\/(\d+))?', message)
        if rating_match or message.startswith('rate '):
            intent['action'] = 'rate'
            # If we have a match, use it
            if rating_match:
                intent['movie_title'] = rating_match.group(1).strip()
                rating = float(rating_match.group(2))
                scale = float(rating_match.group(3) or 5)  # Default to 5 if no scale provided
                intent['rating'] = min(5, (rating / scale) * 5)  # Convert to 5-star scale, max of 5
            else:
                # Try a simpler match for cases like "rate The Shawshank Redemption 5 stars"
                simple_match = re.search(r'rate\s+(?:the\s+)?(?:movie\s+)?([^0-9]+)(\d+(?:\.\d+)?)', message)
                if simple_match:
                    intent['movie_title'] = simple_match.group(1).strip()
                    intent['rating'] = min(5, float(simple_match.group(2)))
            
            self.logger.info(f"Parsed rating intent: {intent}")
            return intent
            
        # Check for popular movies request
        if re.search(r'(popular|top|trending|what.*(watching|good)).*movie', message):
            intent['action'] = 'popular'
            
        # Check for genre-based request
        genre_match = re.search(r'(recommend|suggest|good|watch|find).*(\w+)(?:\s+movies?|\s+films?)', message)
        if genre_match:
            potential_genre = genre_match.group(2).lower()
            self.logger.debug(f"Potential genre detected: {potential_genre}")
            
            # Check if this is a valid genre
            if potential_genre in self.genre_mapping:
                self.logger.info(f"Valid genre detected: {potential_genre}")
                intent['action'] = 'genre'
                intent['genre'] = potential_genre
                
        # Check for direct genre mentions
        for genre_name in self.genre_mapping.keys():
            if genre_name in message.lower():
                self.logger.info(f"Direct genre mention detected: {genre_name}")
                intent['action'] = 'genre'
                intent['genre'] = genre_name
                break
                
        # Check for specific search
        search_match = re.search(r'(find|search|lookup|about).*movie[s]?\s+(?:called|named|titled)?\s+(.+?)(?:$|\?)', message)
        if search_match:
            intent['action'] = 'search'
            intent['query'] = search_match.group(2).strip()
            
        # Check for adding movie to favorites
        favorite_match = re.search(r'add\s+(?:movie\s+)?["\']?([^"\']+)["\']?(?:\s+to\s+(?:my\s+)?favorites)', message)
        if favorite_match:
            intent['action'] = 'add_favorite'
            intent['movie_title'] = favorite_match.group(1).strip()
            
        # Check for recommendation
        if (re.search(r'(recommend|suggest).*movie', message) or 
            re.search(r'what\s+(?:movie|film)\s+should\s+I\s+watch', message)) and intent['action'] is None:
            intent['action'] = 'recommend'
            
            # Try to extract preferences
            if 'like' in message or 'similar to' in message:
                like_match = re.search(r'like\s+["\']?([^"\']+)["\']?(?:$|\?|,|but)', message) or re.search(r'similar to\s+["\']?([^"\']+)["\']?(?:$|\?|,|but)', message)
                if like_match:
                    intent['query'] = like_match.group(1).strip()
                    
        # Default to popular if no clear intent
        if intent['action'] is None:
            intent['action'] = 'popular'
            
        self.logger.info(f"Parsed movie intent: {intent}")
        return intent
    
    async def _get_popular_movies(self) -> Dict[str, Any]:
        """Get popular movies from TMDB"""
        try:
            url = f"{self.base_url}/movie/popular"
            params = {
                'api_key': self.api_key,
                'language': 'en-US',
                'page': 1
            }
            
            self.logger.info(f"Fetching popular movies from TMDB API")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        movies = data.get('results', [])[:5]  # Get top 5 movies
                        
                        self.logger.info(f"Successfully fetched {len(movies)} popular movies")
                        return {
                            'success': True,
                            'movies': movies,
                            'count': len(movies),
                            'category': 'Popular Movies'
                        }
                    else:
                        error_data = await response.text()
                        self.logger.error(f"TMDB API error: {response.status} - {error_data}")
                        return {
                            'success': False,
                            'error': f"Movie API error: {response.status} - {error_data}"
                        }
                        
        except Exception as e:
            self.logger.error(f"Error getting popular movies: {str(e)}")
            return {
                'success': False,
                'error': f"Error fetching popular movies: {str(e)}"
            }
    
    async def _get_movies_by_genre(self, genre: str) -> Dict[str, Any]:
        """Get movies by genre"""
        try:
            genre_id = self.genre_mapping.get(genre.lower())
            
            if not genre_id:
                self.logger.warning(f"Unknown genre: {genre}")
                return {
                    'success': False,
                    'error': f"Unknown genre: {genre}. Try one of: {', '.join(list(self.genre_mapping.keys())[:5])}..."
                }
                
            url = f"{self.base_url}/discover/movie"
            params = {
                'api_key': self.api_key,
                'language': 'en-US',
                'with_genres': genre_id,
                'sort_by': 'popularity.desc',
                'page': 1
            }
            
            self.logger.info(f"Fetching {genre} movies from TMDB API with URL: {url} and genre_id: {genre_id}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        movies = data.get('results', [])[:5]  # Get top 5 movies
                        
                        if not movies:
                            self.logger.warning(f"No {genre} movies found")
                            return {
                                'success': False,
                                'error': f"No {genre} movies found"
                            }
                        
                        self.logger.info(f"Successfully fetched {len(movies)} {genre} movies")
                        return {
                            'success': True,
                            'movies': movies,
                            'count': len(movies),
                            'category': f"{genre.title()} Movies"
                        }
                    else:
                        error_data = await response.text()
                        self.logger.error(f"TMDB API error: {response.status} - {error_data}")
                        return {
                            'success': False,
                            'error': f"Movie API error: {response.status} - {error_data}"
                        }
                        
        except Exception as e:
            self.logger.error(f"Error getting movies by genre: {str(e)}")
            return {
                'success': False,
                'error': f"Error fetching movies by genre: {str(e)}"
            }
    
    async def _search_movies(self, query: str) -> Dict[str, Any]:
        """Search for movies by title"""
        try:
            url = f"{self.base_url}/search/movie"
            params = {
                'api_key': self.api_key,
                'language': 'en-US',
                'query': query,
                'page': 1,
                'include_adult': 'false'
            }
            
            self.logger.info(f"Searching for movies with query: {query}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        movies = data.get('results', [])[:5]  # Get top 5 matches
                        
                        self.logger.info(f"Successfully found {len(movies)} movies matching '{query}'")
                        return {
                            'success': True,
                            'movies': movies,
                            'count': len(movies),
                            'category': f"Search Results for '{query}'"
                        }
                    else:
                        error_data = await response.text()
                        self.logger.error(f"TMDB API error: {response.status} - {error_data}")
                        return {
                            'success': False,
                            'error': f"Movie API error: {response.status} - {error_data}"
                        }
                        
        except Exception as e:
            self.logger.error(f"Error searching movies: {str(e)}")
            return {
                'success': False,
                'error': f"Error searching for movies: {str(e)}"
            }
    
    async def _get_recommendations(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Get movie recommendations based on query or preferences"""
        try:
            recommendations = []
            category = "Recommended Movies"
            
            # If we have a query (movie title to base recommendations on)
            if intent.get('query'):
                # First search for the movie
                search_result = await self._search_movies(intent['query'])
                
                if not search_result.get('success') or search_result.get('count', 0) == 0:
                    # Fall back to personalized recommendations
                    return await self._get_personalized_recommendations()
                    
                # Get the first movie's ID
                movie_id = search_result['movies'][0]['id']
                
                # Now get recommendations for this movie
                url = f"{self.base_url}/movie/{movie_id}/recommendations"
                params = {
                    'api_key': self.api_key,
                    'language': 'en-US',
                    'page': 1
                }
                
                self.logger.info(f"Getting recommendations based on movie ID: {movie_id}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            all_movies = data.get('results', [])
                            
                            # Filter out already watched movies
                            if self.airtable_available:
                                movies = [m for m in all_movies if not self._is_already_watched(m['id'])]
                            else:
                                movies = all_movies
                                
                            if not movies:
                                # Fall back to similar movies if no recommendations or all watched
                                return await self._get_similar_movies(movie_id)
                                
                            base_movie = search_result['movies'][0]['title']
                            self.logger.info(f"Successfully found {len(movies)} recommendations based on '{base_movie}'")
                            
                            recommendations = movies[:5]  # Get top 5 recommendations
                            category = f"Recommendations based on '{base_movie}'"
                        else:
                            # Fall back to similar movies if recommendation API fails
                            return await self._get_similar_movies(movie_id)
            else:
                # Get personalized recommendations
                return await self._get_personalized_recommendations()
                
            # Save these recommendations to Airtable
            if self.airtable_available:
                for movie in recommendations:
                    self._save_recommendation(movie)
            
            return {
                'success': True,
                'movies': recommendations,
                'count': len(recommendations),
                'category': category
            }
                
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {str(e)}")
            return {
                'success': False,
                'error': f"Error fetching recommendations: {str(e)}"
            }
            
    async def _get_personalized_recommendations(self) -> Dict[str, Any]:
        """Get personalized movie recommendations based on user preferences"""
        try:
            recommendations = []
            category = "Recommended Movies For You"
            
            # First try to get recommendations based on favorite genres
            if self.airtable_available:
                favorite_genres = await self._get_favorite_genres()
                
                if favorite_genres:
                    # Use the top genre for recommendations
                    url = f"{self.base_url}/discover/movie"
                    params = {
                        'api_key': self.api_key,
                        'language': 'en-US',
                        'sort_by': 'popularity.desc',
                        'with_genres': ','.join(map(str, favorite_genres)),
                        'page': 1
                    }
                    
                    self.logger.info(f"Getting personalized recommendations based on favorite genres: {favorite_genres}")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                all_movies = data.get('results', [])
                                
                                # Filter out already watched movies
                                movies = [m for m in all_movies if not self._is_already_watched(m['id'])]
                                
                                if movies:
                                    recommendations = movies[:5]  # Get top 5 matches
                                    genre_names = [self.genres.get(genre_id, 'Favorite') for genre_id in favorite_genres if genre_id in self.genres]
                                    category = f"Recommended {', '.join(genre_names[:2])} Movies For You"
            
            # If we don't have recommendations yet, try using popular movies
            if not recommendations:
                popular_result = await self._get_popular_movies()
                if popular_result.get('success'):
                    all_movies = popular_result.get('movies', [])
                    
                    # Filter out already watched movies
                    if self.airtable_available:
                        movies = [m for m in all_movies if not self._is_already_watched(m['id'])]
                    else:
                        movies = all_movies
                        
                    recommendations = movies[:5]
                    category = "Popular Movies You Haven't Seen"
            
            # Save these recommendations to Airtable
            if self.airtable_available:
                for movie in recommendations:
                    self._save_recommendation(movie)
            
            return {
                'success': True,
                'movies': recommendations,
                'count': len(recommendations),
                'category': category
            }
                
        except Exception as e:
            self.logger.error(f"Error getting personalized recommendations: {str(e)}")
            # Fall back to popular movies
            return await self._get_popular_movies()
    
    async def _get_similar_movies(self, movie_id: int) -> Dict[str, Any]:
        """Get similar movies to a given movie ID"""
        try:
            url = f"{self.base_url}/movie/{movie_id}/similar"
            params = {
                'api_key': self.api_key,
                'language': 'en-US',
                'page': 1
            }
            
            self.logger.info(f"Getting similar movies to ID: {movie_id}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        movies = data.get('results', [])[:5]  # Get top 5 similar movies
                        
                        # Get the original movie's title for context
                        movie_url = f"{self.base_url}/movie/{movie_id}"
                        movie_params = {
                            'api_key': self.api_key,
                            'language': 'en-US'
                        }
                        
                        async with session.get(movie_url, params=movie_params) as movie_response:
                            original_movie = None
                            if movie_response.status == 200:
                                movie_data = await movie_response.json()
                                original_movie = movie_data.get('title')
                        
                        self.logger.info(f"Successfully found {len(movies)} similar movies")
                        return {
                            'success': True,
                            'movies': movies,
                            'count': len(movies),
                            'category': f"Movies similar to '{original_movie}'" if original_movie else "Similar Movies"
                        }
                    else:
                        # Fall back to popular if similar API fails
                        return await self._get_popular_movies()
                        
        except Exception as e:
            self.logger.error(f"Error getting similar movies: {str(e)}")
            # Fall back to popular
            return await self._get_popular_movies()
    
    def format_response(self, data: Dict[str, Any]) -> str:
        """Format the movie data for display"""
        if not data.get('success'):
            return f"Sorry, I couldn't find movie recommendations: {data.get('error')}"
            
        if 'message' in data:
            return data['message']
            
        if data.get('count', 0) == 0:
            return "I couldn't find any movies matching your request."
            
        movies = data.get('movies', [])
        category = data.get('category', 'Movies')
        
        result = f"🎬 {category}:\n\n"
        
        for i, movie in enumerate(movies, 1):
            title = movie.get('title', 'Unknown')
            year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A'
            rating = movie.get('vote_average', 0)
            
            # Get genre names from the ids
            genre_ids = movie.get('genre_ids', [])
            genres = [self.genres.get(genre_id, '') for genre_id in genre_ids if genre_id in self.genres]
            genre_text = ', '.join(genres[:2])  # Show up to 2 genres
            
            result += f"{i}. {title} ({year}) - {rating}/10\n"
            if genre_text:
                result += f"   Genres: {genre_text}\n"
            if movie.get('overview'):
                # Truncate overview if too long
                overview = movie['overview']
                if len(overview) > 100:
                    overview = overview[:97] + "..."
                result += f"   {overview}\n"
            
            result += "\n"
            
        return result 
    
    async def _add_to_favorites(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Add a movie to favorites"""
        try:
            if not self.airtable_available:
                return {
                    'success': False,
                    'error': 'Airtable is not available for tracking favorite movies'
                }
                
            if not self.favorites_table_available:
                # Store as a highly rated movie in watched table instead
                self.logger.info("Favorites table not available, adding as highly rated movie in watched table")
                return await self._rate_movie({'movie_title': intent.get('movie_title'), 'rating': 5.0})
            
            movie_title = intent.get('movie_title')
            if not movie_title:
                return {
                    'success': False,
                    'error': 'Please specify a movie title to add to favorites'
                }
                
            # Search for the movie in TMDB
            search_result = await self._search_movies(movie_title)
            if not search_result.get('success') or search_result.get('count', 0) == 0:
                return {
                    'success': False,
                    'error': f"Could not find movie '{movie_title}' in the database"
                }
                
            # Get the first matching movie
            movie = search_result['movies'][0]
            movie_id = str(movie['id'])
            
            # Check if movie already exists in favorites
            try:
                if self.favorites_table_available:
                    existing = self.favorites_table.all(formula=f"{{TMDB_ID}} = '{movie_id}'")
                    if existing:
                        return {
                            'success': True,
                            'message': f"'{movie['title']}' is already in your favorites"
                        }
            except Exception as e:
                self.logger.error(f"Error checking if movie exists in favorites: {e}")
            
            # Get additional movie details like director
            director = await self._get_movie_director(movie['id'])
            
            # Get genre names
            genre_ids = movie.get('genre_ids', [])
            genres = [self.genres.get(genre_id, '') for genre_id in genre_ids if genre_id in self.genres]
            genre_text = ', '.join(genres)
            
            # Add to favorites table
            new_favorite = {
                'TMDB_ID': movie_id,
                'Title': movie['title'],
                'Genres': genre_text
            }
            
            if director:
                new_favorite['Director'] = director
                
            try:
                if self.favorites_table_available:
                    self.favorites_table.create(new_favorite)
                    self.logger.info(f"Added movie to favorites: {movie['title']}")
                    
                    return {
                        'success': True,
                        'message': f"Added '{movie['title']}' to your favorites"
                    }
                else:
                    # Add to watched with high rating as alternative
                    return await self._rate_movie({'movie_title': movie_title, 'rating': 5.0})
            except Exception as e:
                self.logger.error(f"Error adding movie to favorites: {e}")
                return {
                    'success': False,
                    'error': f"Error adding movie to favorites: {str(e)}"
                }
                
        except Exception as e:
            self.logger.error(f"Error adding to favorites: {str(e)}")
            return {
                'success': False,
                'error': f"Error adding movie to favorites: {str(e)}"
            }
    
    async def _rate_movie(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Rate a movie and record it"""
        try:
            if not self.airtable_available or not self.watched_table_available:
                return {
                    'success': False,
                    'error': 'Airtable is not available for tracking movie ratings'
                }
            
            movie_title = intent.get('movie_title')
            rating = intent.get('rating')
            
            if not movie_title or rating is None:
                return {
                    'success': False,
                    'error': 'Please specify a movie title and rating'
                }
                
            # Search for the movie in TMDB
            search_result = await self._search_movies(movie_title)
            if not search_result.get('success') or search_result.get('count', 0) == 0:
                return {
                    'success': False,
                    'error': f"Could not find movie '{movie_title}' in the database"
                }
                
            # Get the first matching movie
            movie = search_result['movies'][0]
            movie_id = str(movie['id'])
            
            # Prepare record to add to watched table
            current_date = datetime.now().strftime('%Y-%m-%d')
            new_watched = {
                'Title': movie['title'],
                'Date Watched': current_date,
                'User Rating': rating
            }
            
            # Try to add the movie to watched table
            try:
                self.watched_table.create(new_watched)
                self.logger.info(f"Added movie to watched list with rating: {movie['title']} - {rating}")
                
                return {
                    'success': True,
                    'message': f"Rated '{movie['title']}' as {rating}/5"
                }
            except Exception as e:
                self.logger.error(f"Error rating movie: {e}")
                
                # If we get a field name error, try different field names
                if "Unknown field name" in str(e):
                    try:
                        # Try with alternative field names
                        alt_watched = {
                            'Name': movie['title'],
                            'Date': current_date,
                            'Rating': rating
                        }
                        self.watched_table.create(alt_watched)
                        self.logger.info(f"Added movie to watched list with alternative field names: {movie['title']} - {rating}")
                        
                        return {
                            'success': True,
                            'message': f"Rated '{movie['title']}' as {rating}/5"
                        }
                    except Exception as e2:
                        self.logger.error(f"Error rating movie with alternative field names: {e2}")
                        return {
                            'success': False,
                            'error': f"Error rating movie: {str(e2)}"
                        }
                
                return {
                    'success': False,
                    'error': f"Error rating movie: {str(e)}"
                }
                
        except Exception as e:
            self.logger.error(f"Error rating movie: {str(e)}")
            return {
                'success': False,
                'error': f"Error rating movie: {str(e)}"
            }
            
    async def _get_movie_director(self, movie_id: int) -> Optional[str]:
        """Get the director for a movie"""
        try:
            url = f"{self.base_url}/movie/{movie_id}/credits"
            params = {
                'api_key': self.api_key,
                'language': 'en-US'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        crew = data.get('crew', [])
                        directors = [member['name'] for member in crew if member.get('job') == 'Director']
                        if directors:
                            return ', '.join(directors)
            return None
        except Exception as e:
            self.logger.error(f"Error getting movie director: {e}")
            return None
    
    def _is_already_watched(self, movie_id: int) -> bool:
        """Check if a movie has already been watched or recommended"""
        if not self.airtable_available or not self.watched_table_available:
            return False
            
        try:
            # Since we don't have TMDB_ID field, we need to check by title
            # For each movie we find, we'll need to compare its title
            # This is less accurate but works with the current table structure
            watched = self.watched_table.all()
            
            # Get the movie details to compare titles
            movie_details = self._get_movie_details_sync(movie_id)
            if not movie_details or 'title' not in movie_details:
                return False
                
            title = movie_details['title'].lower()
            
            # Check if any movie in watched list has a matching title
            for record in watched:
                fields = record.get('fields', {})
                watched_title = fields.get('Title', fields.get('Name', '')).lower()
                if watched_title == title:
                    return True
                    
            return False
        except Exception as e:
            self.logger.error(f"Error checking watched movies: {e}")
            return False
            
    def _get_movie_details_sync(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get movie details synchronously - simplified version for checking watched status"""
        try:
            import requests
            url = f"{self.base_url}/movie/{movie_id}"
            params = {
                'api_key': self.api_key,
                'language': 'en-US'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"Error getting movie details synchronously: {e}")
            return None
            
    def _save_recommendation(self, movie: Dict[str, Any]) -> None:
        """Save a movie that was recommended to the user"""
        if not self.airtable_available or not self.watched_table_available:
            return
            
        try:
            # Check if movie already exists
            if self._is_already_watched(movie['id']):
                return
                
            # Add to watched table with recommended date
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            try:
                self.watched_table.create({
                    'Title': movie['title'],
                    'Date Recommended': current_date
                })
            except Exception as e:
                if "Unknown field name" in str(e):
                    # Try alternative field names
                    self.watched_table.create({
                        'Name': movie['title'],
                        'Date': current_date
                    })
                else:
                    raise e
                    
            self.logger.info(f"Saved recommendation: {movie['title']}")
        except Exception as e:
            self.logger.error(f"Error saving recommendation: {e}")
            
    async def _get_favorite_genres(self) -> List[int]:
        """Extract favorite genres from saved movies"""
        if not self.airtable_available:
            return []
            
        try:
            genre_counts = {}
            
            # Process favorites if available
            if self.favorites_table_available:
                try:
                    favorites = self.favorites_table.all()
                    
                    # Process favorites
                    for movie in favorites:
                        genres = movie['fields'].get('Genres', '').split(',')
                        for genre in genres:
                            genre = genre.strip()
                            if genre:
                                # Convert genre name to ID
                                for genre_name, genre_id in self.genre_mapping.items():
                                    if genre.lower() == genre_name:
                                        genre_counts[genre_id] = genre_counts.get(genre_id, 0) + 2  # More weight for favorites
                except Exception as e:
                    self.logger.error(f"Error getting favorite genres from favorites table: {e}")
            
            # Get details for highly rated movies (4+)
            try:
                # Try to determine which rating field to use
                # First, check if we can get a sample record to see field names
                try:
                    sample_records = self.watched_table.all(max_records=1)
                    if sample_records:
                        fields = sample_records[0].get('fields', {})
                        
                        # Check which rating field exists
                        rating_field = None
                        if 'User Rating' in fields:
                            rating_field = 'User Rating'
                        elif 'Rating' in fields:
                            rating_field = 'Rating'
                        
                        if rating_field:
                            # Use the appropriate field in the formula
                            formula = f"{{{rating_field}}} >= 4"
                            watched = self.watched_table.all(formula=formula)
                            
                            # Get details for watched movies to extract genres
                            for movie in watched:
                                fields = movie.get('fields', {})
                                title = fields.get('Title', fields.get('Name', ''))
                                
                                if title:
                                    # Search for the movie in TMDB to get genre information
                                    search_url = f"{self.base_url}/search/movie"
                                    params = {
                                        'api_key': self.api_key,
                                        'language': 'en-US',
                                        'query': title,
                                        'page': 1,
                                        'include_adult': 'false'
                                    }
                                    
                                    async with aiohttp.ClientSession() as session:
                                        async with session.get(search_url, params=params) as response:
                                            if response.status == 200:
                                                data = await response.json()
                                                results = data.get('results', [])
                                                
                                                if results:
                                                    # Use the first matching movie's genre information
                                                    movie_genres = results[0].get('genre_ids', [])
                                                    for genre_id in movie_genres:
                                                        if genre_id in self.genres:  # Make sure it's a valid genre
                                                            genre_counts[genre_id] = genre_counts.get(genre_id, 0) + 1
                    else:
                        self.logger.warning("No sample records found to determine rating field")
                        await self._get_genre_counts_from_all_watched(genre_counts)
                except Exception as e:
                    self.logger.error(f"Error determining rating field: {e}")
                    # If we can't determine fields, try with some defaults
                    await self._get_genre_counts_from_all_watched(genre_counts)
            except Exception as e:
                self.logger.error(f"Error getting favorite genres from watched table: {e}")
                # Try to get genre counts from all watched movies if formula doesn't work
                await self._get_genre_counts_from_all_watched(genre_counts)
            
            # Sort by count and return top genre IDs
            sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
            return [genre_id for genre_id, count in sorted_genres[:3]]
        except Exception as e:
            self.logger.error(f"Error getting favorite genres: {e}")
            return []
            
    async def _get_genre_counts_from_all_watched(self, genre_counts: Dict[int, int]) -> None:
        """Get genre counts from all watched movies as a fallback"""
        try:
            watched = self.watched_table.all()
            
            for movie in watched:
                fields = movie.get('fields', {})
                title = fields.get('Title', fields.get('Name', ''))
                
                if title:
                    # Search for the movie in TMDB to get genre information
                    search_url = f"{self.base_url}/search/movie"
                    params = {
                        'api_key': self.api_key,
                        'language': 'en-US',
                        'query': title,
                        'page': 1,
                        'include_adult': 'false'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(search_url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                results = data.get('results', [])
                                
                                if results:
                                    # Use the first matching movie's genre information
                                    movie_genres = results[0].get('genre_ids', [])
                                    for genre_id in movie_genres:
                                        if genre_id in self.genres:  # Make sure it's a valid genre
                                            genre_counts[genre_id] = genre_counts.get(genre_id, 0) + 1
        except Exception as e:
            self.logger.error(f"Error getting genre counts from all watched movies: {e}")
            
    async def _get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a movie"""
        try:
            url = f"{self.base_url}/movie/{movie_id}"
            params = {
                'api_key': self.api_key,
                'language': 'en-US'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except Exception as e:
            self.logger.error(f"Error getting movie details: {e}")
            return None

    def prepare_movie_data_for_assistant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare movie data to be passed to the assistant as structured data"""
        assistant_data = {
            'type': 'movie_recommendations',
            'success': data.get('success', False),
            'timestamp': datetime.now().isoformat()
        }
        
        if not data.get('success', False):
            assistant_data['error'] = data.get('error', 'Unknown error')
            return assistant_data
            
        if 'message' in data:
            assistant_data['message'] = data['message']
            return assistant_data
            
        # Add category and count information
        assistant_data['category'] = data.get('category', 'Movies')
        assistant_data['count'] = data.get('count', 0)
        
        # Format movie details for structured data
        movies = []
        for movie in data.get('movies', []):
            movie_data = {
                'title': movie.get('title', 'Unknown'),
                'id': movie.get('id'),
                'year': movie.get('release_date', '')[:4] if movie.get('release_date') else None,
                'rating': movie.get('vote_average', 0),
                'overview': movie.get('overview'),
                'genres': []
            }
            
            # Add genre information
            genre_ids = movie.get('genre_ids', [])
            for genre_id in genre_ids:
                if genre_id in self.genres:
                    movie_data['genres'].append(self.genres[genre_id])
            
            # Add poster path if available
            if movie.get('poster_path'):
                movie_data['poster_url'] = f"{self.image_base_url}{movie['poster_path']}"
                
            movies.append(movie_data)
            
        assistant_data['movies'] = movies
        
        return assistant_data 