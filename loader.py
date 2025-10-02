import json
from datetime import datetime
import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def main():
    print("Loading data to Supabase...")
    
    try:
        # Load JSON data directly (no pandas)
        with open("data/menu_data.json", "r") as f:
            menu_items = json.load(f)
        
        # Connect to Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        successful = 0
        for item in menu_items:
            try:
                # Add current timestamp
                item['updated_at'] = datetime.now().isoformat()
                
                # Ensure extracted_at is string
                if 'extracted_at' in item and hasattr(item['extracted_at'], 'isoformat'):
                    item['extracted_at'] = item['extracted_at'].isoformat()
                
                # Upsert to Supabase
                response = supabase.table('chickfila_menu').upsert(item).execute()
                
                if not hasattr(response, 'error') or not response.error:
                    successful += 1
                    print(f"✓ {item['name']}")
                else:
                    print(f"✗ {item['name']}: {response.error}")
                    
            except Exception as e:
                print(f"Error with {item.get('name', 'unknown')}: {e}")
        
        print(f"\nSuccessfully loaded {successful}/{len(menu_items)} items!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()