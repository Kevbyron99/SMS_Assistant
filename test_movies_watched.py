import os
from dotenv import load_dotenv
from pyairtable import Api
import sys
from datetime import datetime

# Load environment variables
load_dotenv()

def test_movies_watched():
    """Test adding a record directly to the Movies Watched table"""
    print("Testing Movies Watched Table...")
    
    # Get credentials from environment
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    watched_table = os.getenv('AIRTABLE_MOVIES_WATCHED', 'Movies Watched')
    
    if not api_key:
        print("ERROR: Airtable API key not found in .env file")
        return False
        
    if not base_id:
        print("ERROR: Airtable Base ID not found in .env file")
        return False
        
    print(f"Airtable API Key: {api_key[:5]}...{api_key[-5:]}")
    print(f"Airtable Base ID: {base_id}")
    print(f"Airtable Movies Watched Table: {watched_table}")
    
    try:
        # Connect to Airtable
        print("\nConnecting to Airtable...")
        api = Api(api_key)
        base = api.base(base_id)
        table = base.table(watched_table)
        
        # Get table schema to see field names
        print("\nGetting field names from Movies Watched table:")
        try:
            schema = table.schema()
            fields = schema.get('fields', [])
            if fields:
                print(f"Found {len(fields)} fields:")
                for field in fields:
                    print(f"- {field.get('name')} ({field.get('type')})")
            else:
                print("No fields found in schema")
            
            # Also try getting a record to see field names
            records = table.all(max_records=1)
            if records:
                print("\nField names from first record:")
                fields = records[0].get('fields', {})
                for field_name in fields.keys():
                    print(f"- {field_name}")
            
        except Exception as e:
            print(f"Error getting schema: {e}")
        
        # List existing records
        print("\nListing existing records in Movies Watched table:")
        records = table.all(max_records=5)
        if records:
            print(f"Found {len(records)} records:")
            for i, record in enumerate(records, 1):
                fields = record['fields']
                title = fields.get('Title', fields.get('Name', 'No Title'))
                date = fields.get('Date Watched', fields.get('Date', 'No date'))
                print(f"{i}. {title} - {date}")
        else:
            print("No records found in the table")
        
        # Add a test movie using detected field names
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\nAdding test movie to {watched_table} table...")
        new_movie = {
            'Title': f"Test Movie {current_date}",
            'Date Watched': current_date,
            'User Rating': 4.5
        }
        
        # If we found the first record, try to match its field names
        if records and records[0].get('fields'):
            field_names = records[0].get('fields', {}).keys()
            # Map our fields to existing field names
            if 'Title' not in field_names and 'Name' in field_names:
                new_movie['Name'] = new_movie.pop('Title')
            if 'Date Watched' not in field_names and 'Date' in field_names:
                new_movie['Date'] = new_movie.pop('Date Watched')
            if 'User Rating' not in field_names and 'Rating' in field_names:
                new_movie['Rating'] = new_movie.pop('User Rating')
        
        print("Adding record with fields:", new_movie)
        record = table.create(new_movie)
        print(f"Successfully added: {new_movie.get('Title', new_movie.get('Name', 'Test Movie'))}")
        print(f"Record ID: {record['id']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_movies_watched()
    sys.exit(0 if success else 1) 