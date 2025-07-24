#!/usr/bin/env python3
"""
Check for more granular fixture difficulty data and team strength metrics
"""
import requests
import pandas as pd
import json

def explore_detailed_fixture_data():
    """Explore all available fixture and team strength data"""
    
    print("🔍 EXPLORING GRANULAR FIXTURE DIFFICULTY DATA")
    print("=" * 60)
    
    try:
        # Get bootstrap data
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
        data = response.json()
        
        print("\n📊 TEAM STRENGTH DATA:")
        teams_df = pd.DataFrame(data['teams'])
        
        # Check team strength columns
        strength_columns = [col for col in teams_df.columns if 'strength' in col.lower()]
        print(f"Available strength metrics: {strength_columns}")
        
        if strength_columns:
            print("\nSample team strength data:")
            sample_teams = teams_df[['name'] + strength_columns].head(5)
            for _, team in sample_teams.iterrows():
                print(f"\n{team['name']}:")
                for col in strength_columns:
                    print(f"  {col}: {team[col]}")
        
        print(f"\n📋 FIXTURES DATA STRUCTURE:")
        # Get fixtures
        fixtures_response = requests.get("https://fantasy.premierleague.com/api/fixtures/", timeout=10)
        fixtures_data = fixtures_response.json()
        
        if fixtures_data:
            sample_fixture = fixtures_data[0]
            print(f"Available fixture fields: {list(sample_fixture.keys())}")
            
            # Look for difficulty-related fields
            difficulty_fields = [field for field in sample_fixture.keys() if 'difficulty' in field.lower()]
            print(f"Difficulty fields: {difficulty_fields}")
            
            # Look for strength-related fields
            strength_fields = [field for field in sample_fixture.keys() if 'strength' in field.lower()]
            print(f"Strength fields in fixtures: {strength_fields}")
            
            print(f"\nSample fixture data:")
            for field in ['team_h', 'team_a', 'team_h_difficulty', 'team_a_difficulty', 'team_h_score', 'team_a_score']:
                if field in sample_fixture:
                    print(f"  {field}: {sample_fixture[field]}")
        
        print(f"\n🎯 CALCULATING CUSTOM DIFFICULTY METRICS:")
        
        # Calculate more granular difficulty based on team strengths
        teams_df = pd.DataFrame(data['teams'])
        fixtures_df = pd.DataFrame(fixtures_data)
        
        # Create custom difficulty based on multiple factors
        def calculate_granular_difficulty(team_h_id, team_a_id, venue='home'):
            team_h = teams_df[teams_df['id'] == team_h_id].iloc[0]
            team_a = teams_df[teams_df['id'] == team_a_id].iloc[0]
            
            if venue == 'home':
                # For home team
                attacking_difficulty = (6 - team_a['strength_defence_home']) / 5 * 10  # Scale to 0-10
                defensive_difficulty = team_a['strength_attack_away'] / 5 * 10
            else:
                # For away team  
                attacking_difficulty = (6 - team_h['strength_defence_away']) / 5 * 10
                defensive_difficulty = team_h['strength_attack_home'] / 5 * 10
            
            # Combined difficulty (higher = harder)
            overall_difficulty = (attacking_difficulty + defensive_difficulty) / 2
            
            return {
                'attacking_difficulty': attacking_difficulty,
                'defensive_difficulty': defensive_difficulty, 
                'overall_difficulty': overall_difficulty
            }
        
        # Test with a few fixtures
        print("\nSample granular difficulty calculations:")
        for i, fixture in enumerate(fixtures_data[:3]):
            if fixture['team_h'] and fixture['team_a']:
                team_h_name = teams_df[teams_df['id'] == fixture['team_h']]['name'].iloc[0]
                team_a_name = teams_df[teams_df['id'] == fixture['team_a']]['name'].iloc[0]
                
                home_difficulty = calculate_granular_difficulty(fixture['team_h'], fixture['team_a'], 'home')
                away_difficulty = calculate_granular_difficulty(fixture['team_h'], fixture['team_a'], 'away')
                
                print(f"\nFixture: {team_h_name} vs {team_a_name}")
                print(f"  FPL Difficulty - Home: {fixture['team_h_difficulty']}, Away: {fixture['team_a_difficulty']}")
                print(f"  Custom Difficulty - {team_h_name} (H): {home_difficulty['overall_difficulty']:.2f}")
                print(f"  Custom Difficulty - {team_a_name} (A): {away_difficulty['overall_difficulty']:.2f}")
        
        print(f"\n✅ AVAILABLE GRANULAR METRICS:")
        print("1. Team strength_attack_home/away (1-5 scale)")
        print("2. Team strength_defence_home/away (1-5 scale)")  
        print("3. Team strength_overall_home/away (1-5 scale)")
        print("4. Custom calculated difficulty (0-10 scale)")
        print("5. Attack/Defense specific difficulty")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    explore_detailed_fixture_data()