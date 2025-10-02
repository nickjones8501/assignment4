import openai 
from openai import OpenAI
import json
import os
from datetime import datetime

# Your provided configuration
endpoint = "https://cdong1--azure-proxy-web-app.modal.run"
api_key = "supersecretkey"
deployment_name = "gpt-4o"

client = OpenAI(
    base_url=endpoint,
    api_key=api_key
)

def structure_menu_simple(text_blob):
    """Simple menu structuring with LLM"""
    
    prompt = f"""
    Extract Chick-fil-A menu items from this text and return as JSON array.
    
    Text: {text_blob[:4000]}
    
    Return JSON format like this:
    [
        {{
            "id": "waffle-fries",
            "name": "Waffle Potato Fries",
            "category": "sides",
            "description": "Freshly cooked waffle-cut fries",
            "price": "$2.50",
            "calories": "360",
            "allergens": ["wheat", "dairy"],
            "is_vegetarian": false,
            "is_gluten_free": false
        }}
    ]
    
    Extract all menu items you find. If information is missing, make reasonable estimates.
    Return ONLY valid JSON, no other text.
    """
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        result = response.choices[0].message.content.strip()
        
        # Clean JSON response
        if result.startswith('```json'):
            result = result[7:]
        if result.endswith('```'):
            result = result[:-3]
        
        # Parse and validate JSON
        menu_data = json.loads(result)
        
        # Add metadata
        for item in menu_data:
            item['source_url'] = 'https://www.chick-fil-a.com/menu/sides'
            item['extracted_at'] = datetime.now().isoformat()
        
        return menu_data
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def save_json(data, filename="data/menu_data.json"):
    """Save data to JSON file"""
    os.makedirs("data", exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} items to {filename}")

if __name__ == "__main__":
    try:
        with open("data/raw_blob.txt", "r") as f:
            text = f.read()
        
        menu_items = structure_menu_simple(text)
        if menu_items:
            save_json(menu_items)
            print("Success! Menu data structured.")
        else:
            print("No data extracted")
    except FileNotFoundError:
        print("Run collector.py first!")