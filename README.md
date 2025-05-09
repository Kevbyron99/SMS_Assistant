# Personal Assistant

This is a personal assistant that can help you with various tasks, including:
- Managing shifts and scheduling
- Getting weather information  
- Finding train times and transport information
- Movie recommendations and tracking

## Setting Up

1. Create a `.env` file based on the `.env.example` template
2. Add your API keys for different services
3. Run the assistant with `python app.py`

## Shift Tracking

The assistant can help you track your shifts using Airtable. You can:
- Add a new shift with specific dates and times
- Mark a day as off
- List all shifts
- Check your next shift

Example commands:
- "Add a shift on Monday from 9am to 5pm"
- "Mark Tuesday as a day off"
- "What shifts do I have this week?"
- "When is my next shift?"

## Movie Recommendations

The assistant can help you find movies to watch and track your favorites.

### Features:
- Recommend popular movies or movies in specific genres
- Find movies similar to ones you like
- Rate movies you've watched
- Track your favorites
- Personalized recommendations based on your preferences

### Setup:
1. Get an API key from [TMDB](https://www.themoviedb.org/settings/api)
2. Set up an Airtable base with a "Movies Watched" table
3. Add the API keys to your `.env` file

### Example commands:
- "Recommend popular movies"
- "Recommend comedy movies"
- "Recommend movies similar to The Dark Knight"
- "Rate Inception 4.5/5"
- "Add The Shawshank Redemption to my favorites" #   P e r s o n a l _ a s s i s t a n t  
 #   S M S _ A s s i s t a n t  
 #   S M S _ A s s i s t a n t  
 