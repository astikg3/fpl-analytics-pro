#!/usr/bin/env python3
import requests
import json
from pprint import pprint

def explore_fpl_api():
    """Comprehensive exploration of FPL API endpoints and data structure"""
    
    print("🔍 EXPLORING FPL API DATA STRUCTURE")
    print("=" * 50)
    
    # Main bootstrap endpoint
    try:
        print("\n📊 BOOTSTRAP-STATIC DATA:")
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        print(f"✅ Main API Keys: {list(data.keys())}")
        
        # Explore each section
        sections = {
            'events': 'Gameweeks',
            'game_settings': 'Game Settings', 
            'phases': 'Phases',
            'teams': 'Premier League Teams',
            'total_players': 'Total FPL Players',
            'elements': 'Player Data',
            'element_stats': 'Player Statistics Categories',
            'element_types': 'Positions (GK, DEF, MID, FWD)'
        }
        
        for key, description in sections.items():
            if key in data:
                if isinstance(data[key], list) and data[key]:
                    print(f"\n📋 {description} ({key}): {len(data[key])} items")
                    if key == 'elements':
                        # Show player data structure
                        sample_player = data[key][0]
                        print("   Sample player fields:")
                        for field in sorted(sample_player.keys())[:15]:
                            print(f"     • {field}: {sample_player[field]}")
                        print(f"     ... and {len(sample_player.keys())-15} more fields")
                        
                    elif key == 'teams':
                        print("   Teams:")
                        for team in data[key][:5]:
                            print(f"     • {team['name']} (id: {team['id']})")
                        print(f"     ... and {len(data[key])-5} more teams")
                        
                    elif key == 'events':
                        current_gw = next((gw for gw in data[key] if gw['is_current']), None)
                        if current_gw:
                            print(f"   Current Gameweek: {current_gw['id']} - {current_gw['name']}")
                        finished_gws = [gw for gw in data[key] if gw['finished']]
                        print(f"   Finished Gameweeks: {len(finished_gws)}")
                        
                    elif key == 'element_types':
                        print("   Positions:")
                        for pos in data[key]:
                            print(f"     • {pos['singular_name']} ({pos['plural_name_short']})")
                            
                else:
                    print(f"\n📋 {description} ({key}): {data[key]}")
                    
        # Current gameweek details
        current_gw = next((gw for gw in data['events'] if gw['is_current']), None)
        if current_gw:
            print(f"\n🏆 CURRENT GAMEWEEK {current_gw['id']} DETAILS:")
            print(f"   Name: {current_gw['name']}")
            print(f"   Deadline: {current_gw['deadline_time']}")
            print(f"   Finished: {current_gw['finished']}")
            print(f"   Average Score: {current_gw.get('average_entry_score', 'N/A')}")
            print(f"   Highest Score: {current_gw.get('highest_score', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error fetching bootstrap data: {e}")
    
    # Explore other endpoints
    other_endpoints = [
        ("fixtures/", "All fixtures"),
        ("dream-team/", "Dream team for current gameweek"),
    ]
    
    print(f"\n🌐 OTHER AVAILABLE ENDPOINTS:")
    base_url = "https://fantasy.premierleague.com/api"
    
    for endpoint, description in other_endpoints:
        try:
            url = f"{base_url}/{endpoint}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ {endpoint} ({description}): {len(data)} items")
                    if endpoint == "fixtures/" and data:
                        print(f"   Sample fixture fields: {list(data[0].keys())[:8]}...")
                else:
                    print(f"✅ {endpoint} ({description}): Available")
            else:
                print(f"❌ {endpoint}: Status {response.status_code}")
        except:
            print(f"❌ {endpoint}: Connection failed")
    
    # Player-specific endpoints (need player ID)
    print(f"\n👤 PLAYER-SPECIFIC ENDPOINTS (require player ID):")
    try:
        # Get a sample player ID
        bootstrap_data = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
        sample_player_id = bootstrap_data['elements'][0]['id']
        
        player_endpoints = [
            (f"element-summary/{sample_player_id}/", "Player history & fixtures"),
        ]
        
        for endpoint, description in player_endpoints:
            try:
                url = f"{base_url}/{endpoint}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint} ({description})")
                    print(f"   Keys: {list(data.keys())}")
                    if 'history' in data and data['history']:
                        print(f"   Historical data points: {len(data['history'])}")
                    if 'fixtures' in data:
                        print(f"   Upcoming fixtures: {len(data['fixtures'])}")
            except:
                print(f"❌ {endpoint}: Failed")
                
    except Exception as e:
        print(f"❌ Error exploring player endpoints: {e}")
    
    # Gameweek-specific endpoints
    print(f"\n📅 GAMEWEEK-SPECIFIC ENDPOINTS:")
    try:
        current_gw_id = 1  # Try gameweek 1
        gw_endpoints = [
            (f"event/{current_gw_id}/live/", "Live gameweek data"),
        ]
        
        for endpoint, description in gw_endpoints:
            try:
                url = f"{base_url}/{endpoint}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint} ({description})")
                    print(f"   Keys: {list(data.keys())}")
                    if 'elements' in data:
                        print(f"   Player performance data: {len(data['elements'])} players")
            except:
                print(f"❌ {endpoint}: Failed")
                
    except Exception as e:
        print(f"❌ Error exploring gameweek endpoints: {e}")

    print(f"\n🎯 SUMMARY:")
    print("The FPL API provides:")
    print("• 📊 Player stats (points, price, form, ICT index)")
    print("• 🏟️  Team information")
    print("• 📅 Gameweek schedules and results")
    print("• 🎯 Fixtures and difficulty ratings")
    print("• 📈 Historical player performance")
    print("• 🏆 Dream team selections")
    print("• 💰 Price changes and ownership")

if __name__ == "__main__":
    explore_fpl_api()