import dash
from dash import html
import requests
import pandas as pd

app = dash.Dash(__name__)

# Simple test data load
try:
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url, timeout=5)
    data = response.json()
    player_count = len(data['elements'])
    status = "✅ API Connected"
except:
    player_count = 0
    status = "❌ API Failed"

app.layout = html.Div([
    html.H1("FPL Dashboard Test"),
    html.P(f"Status: {status}"),
    html.P(f"Players loaded: {player_count}")
])

if __name__ == "__main__":
    print("Starting minimal test...")
    app.run_server(debug=False, host='0.0.0.0', port=8051)