import os
from dotenv import load_dotenv
from pyairtable import Api
import sys

# Load environment variables
load_dotenv()

def test_airtable_connection():
    """Test connection to Airtable and list tables in the base"""
    print("Testing Airtable Connection...")
    
    # Get credentials from environment
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key:
        print("ERROR: Airtable API key not found in .env file")
        return False
        
    if not base_id:
        print("ERROR: Airtable Base ID not found in .env file")
        return False
        
    print(f"Airtable API Key: {api_key[:5]}...{api_key[-5:]}")
    print(f"Airtable Base ID: {base_id}")
    
    try:
        # Connect to Airtable using modern API approach
        print("\nConnecting to Airtable...")
        api = Api(api_key)
        
        # Get the base
        base = api.base(base_id)
        
        # List all table IDs in the base
        print("\nListing tables in the base:")
        try:
            tables = list(base.tables)
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"- {table['name']} (ID: {table['id']})")
        except Exception as e:
            print(f"ERROR: Failed to list tables: {e}")
            
            # Try direct access to tables we need
            print("\nAttempting direct table access:")
            favorites_table = os.getenv('AIRTABLE_MOVIE_FAVORITES', 'Movie Favorites')
            watched_table = os.getenv('AIRTABLE_MOVIES_WATCHED', 'Movies Watched')
            
            try:
                # Try to access favorites table
                table = base.table(favorites_table)
                print(f"Successfully accessed {favorites_table} table")
                
                # Try to list records
                try:
                    records = table.all(max_records=1)
                    print(f"- Found {len(records)} records in {favorites_table}")
                except Exception as e:
                    print(f"- Failed to list records in {favorites_table}: {e}")
            except Exception as e:
                print(f"Failed to access {favorites_table} table: {e}")
                
            try:
                # Try to access watched table
                table = base.table(watched_table)
                print(f"Successfully accessed {watched_table} table")
                
                # Try to list records
                try:
                    records = table.all(max_records=1)
                    print(f"- Found {len(records)} records in {watched_table}")
                except Exception as e:
                    print(f"- Failed to list records in {watched_table}: {e}")
            except Exception as e:
                print(f"Failed to access {watched_table} table: {e}")
                
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to connect to Airtable: {e}")
        return False

if __name__ == "__main__":
    success = test_airtable_connection()
    sys.exit(0 if success else 1) 