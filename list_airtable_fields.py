import os
from dotenv import load_dotenv
from pyairtable import Table

# Load environment variables
load_dotenv()

def list_airtable_fields():
    """List the fields in the Airtable Shifts table"""
    
    # Get Airtable credentials from environment variables
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_SHIFTS_TABLE', 'Shifts')
    
    if not api_key or not base_id:
        print("Error: Missing Airtable credentials in .env file")
        return
    
    print(f"Connecting to Airtable base {base_id}, table {table_name}")
    
    try:
        # Connect to Airtable
        table = Table(api_key, base_id, table_name)
        
        # Get a record to see fields
        records = table.all(max_records=1)
        
        if not records:
            print("No records found in the table. Creating a sample record to view fields...")
            
            # Create a sample record to see field names
            sample = {
                'ID': 'sample',
                'Date': '2023-03-24',
                'Start Time': '09:00',
                'End Time': '17:00'
            }
            
            try:
                table.create(sample)
                print("Sample record created.")
                records = table.all(max_records=1)
            except Exception as e:
                print(f"Error creating sample record: {e}")
        
        if records:
            print("\nFields in the Shifts table:")
            fields = list(records[0]['fields'].keys())
            for i, field in enumerate(fields, 1):
                print(f"{i}. {field}")
            
            # Show field types if possible
            print("\nField details:")
            for field in fields:
                field_value = records[0]['fields'].get(field)
                field_type = type(field_value).__name__
                print(f"{field}: {field_type} - Example: {field_value}")
        else:
            print("Could not retrieve field information. No records in table.")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_airtable_fields() 