import requests
import json

def test_fpl_api():
    """Test FPL API connection and data structure"""
    try:
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        print("✅ API connection successful!")
        print(f"Players: {len(data['elements'])}")
        print(f"Teams: {len(data['teams'])}")
        print(f"Positions: {len(data['element_types'])}")
        
        # Check first player structure
        first_player = data['elements'][0]
        print(f"\nFirst player keys: {list(first_player.keys())[:10]}...")
        
        # Check if required fields exist
        required_fields = ['web_name', 'team', 'element_type', 'now_cost', 'total_points']
        missing_fields = [field for field in required_fields if field not in first_player]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
        else:
            print("✅ All required fields present")
            
        return True
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        return False

if __name__ == "__main__":
    test_fpl_api()