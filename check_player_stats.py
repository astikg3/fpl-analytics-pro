#!/usr/bin/env python3
import requests
import pandas as pd
from pprint import pprint

def check_player_stats():
    """Check available player statistics in FPL API"""
    
    print("🔍 PLAYER STATISTICS AVAILABLE IN FPL API")
    print("=" * 50)
    
    try:
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
        data = response.json()
        
        # Get sample player
        sample_player = data['elements'][0]
        
        print(f"📊 Total fields available per player: {len(sample_player.keys())}")
        print("\n🏆 KEY STATISTICS FIELDS:")
        
        # Categorize statistics
        stats_categories = {
            "💰 Financial": ["now_cost", "cost_change_event", "cost_change_start", "selected_by_percent", "transfers_in", "transfers_out", "transfers_in_event", "transfers_out_event"],
            "⚽ Performance": ["total_points", "points_per_game", "form", "goals_scored", "assists", "clean_sheets", "goals_conceded", "own_goals", "penalties_saved", "penalties_missed", "yellow_cards", "red_cards", "saves", "bonus", "bps"],
            "📈 Advanced": ["ict_index", "influence", "creativity", "threat", "minutes", "starts", "expected_goals", "expected_assists", "expected_goal_involvements", "expected_goals_conceded"],
            "🎯 Meta": ["web_name", "first_name", "second_name", "team", "element_type", "status", "chance_of_playing_this_round", "chance_of_playing_next_round"],
            "📊 Per 90": ["goals_scored_per_90", "assists_per_90", "clean_sheets_per_90", "goals_conceded_per_90", "saves_per_90", "expected_goals_per_90", "expected_assists_per_90", "expected_goal_involvements_per_90", "expected_goals_conceded_per_90"]
        }
        
        for category, fields in stats_categories.items():
            print(f"\n{category}:")
            available_fields = [field for field in fields if field in sample_player]
            for field in available_fields:
                value = sample_player[field]
                print(f"  • {field}: {value}")
            
            missing_fields = [field for field in fields if field not in sample_player]
            if missing_fields:
                print(f"  ❌ Missing: {missing_fields}")
        
        print(f"\n🔢 SAMPLE VALUES FOR TOP SCORER:")
        # Find top scorer
        players_df = pd.DataFrame(data['elements'])
        top_scorer = players_df.loc[players_df['total_points'].idxmax()]
        
        print(f"Player: {top_scorer['web_name']}")
        print(f"Points: {top_scorer['total_points']}")
        print(f"Goals: {top_scorer['goals_scored']}")
        print(f"Assists: {top_scorer['assists']}")
        print(f"Price: £{top_scorer['now_cost']/10}m")
        print(f"Form: {top_scorer['form']}")
        print(f"ICT Index: {top_scorer['ict_index']}")
        print(f"Expected Goals: {top_scorer.get('expected_goals', 'N/A')}")
        print(f"Expected Assists: {top_scorer.get('expected_assists', 'N/A')}")
        print(f"Minutes: {top_scorer['minutes']}")
        print(f"Ownership: {top_scorer['selected_by_percent']}%")
        
        print(f"\n📋 ALL AVAILABLE FIELDS:")
        all_fields = sorted(sample_player.keys())
        for i, field in enumerate(all_fields):
            if i % 4 == 0:
                print()
            print(f"{field:25}", end="")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_player_stats()