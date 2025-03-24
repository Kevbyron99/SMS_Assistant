import os
from dotenv import load_dotenv
from pyairtable import Api

# Load environment variables
load_dotenv()

def check_watched_movies():
    print("Checking watched movies in Airtable...")
    
    # Get Airtable credentials
    airtable_api_key = os.getenv("AIRTABLE_API_KEY")
    airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
    watched_table = os.getenv("AIRTABLE_MOVIES_WATCHED", "Movies Watched")
    
    if not all([airtable_api_key, airtable_base_id, watched_table]):
        print("Airtable configuration missing. Please check your .env file.")
        return
    
    print(f"Airtable API Key: {'Available' if airtable_api_key else 'Missing'}")
    print(f"Airtable Base ID: {'Available' if airtable_base_id else 'Missing'}")
    print(f"Movies Watched Table: {'Available' if watched_table else 'Missing'}")
    
    try:
        # Connect to Airtable
        api = Api(airtable_api_key)
        base = api.base(airtable_base_id)
        table = base.table(watched_table)
        
        # Get all records
        records = table.all()
        
        print(f"\nFound {len(records)} watched movies in Airtable:")
        
        for record in records:
            fields = record.get('fields', {})
            title = fields.get('Title', fields.get('Name', 'Unknown'))
            date_watched = fields.get('Date Watched', fields.get('Date', 'Unknown'))
            rating = fields.get('User Rating', fields.get('Rating', 'Not rated'))
            
            print(f"- {title} (Watched: {date_watched}, Rating: {rating})")
            
    except Exception as e:
        print(f"Error checking watched movies: {str(e)}")

if __name__ == "__main__":
    check_watched_movies() 