import requests
import pandas as pd
import json
from typing import Dict, List, Optional

class FPLDataScraper:
    def __init__(self):
        self.base_url = "https://fantasy.premierleague.com/api"
        self.session = requests.Session()
        
    def get_general_info(self) -> Dict:
        """Get general FPL information including teams, players, and gameweeks."""
        url = f"{self.base_url}/bootstrap-static/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_player_data(self) -> pd.DataFrame:
        """Extract player data and return as DataFrame."""
        data = self.get_general_info()
        players_df = pd.DataFrame(data['elements'])
        teams_df = pd.DataFrame(data['teams'])
        positions_df = pd.DataFrame(data['element_types'])
        
        # Create mapping dictionaries
        team_map = dict(zip(teams_df['id'], teams_df['name']))
        position_map = dict(zip(positions_df['id'], positions_df['singular_name']))
        
        # Map team and position names
        players_df['team_name'] = players_df['team'].map(team_map)
        players_df['position'] = players_df['element_type'].map(position_map)
        
        return players_df
    
    def get_gameweek_data(self, gameweek: int) -> Dict:
        """Get data for a specific gameweek."""
        url = f"{self.base_url}/event/{gameweek}/live/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_player_history(self, player_id: int) -> Dict:
        """Get historical data for a specific player."""
        url = f"{self.base_url}/element-summary/{player_id}/"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_top_performers(self, metric: str = 'total_points', limit: int = 20) -> pd.DataFrame:
        """Get top performing players by specified metric."""
        players_df = self.get_player_data()
        return players_df.nlargest(limit, metric)
    
    def save_data(self, filename: str, data: pd.DataFrame):
        """Save DataFrame to CSV file."""
        data.to_csv(f"data/{filename}", index=False)
        print(f"Data saved to data/{filename}")