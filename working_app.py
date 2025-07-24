#!/usr/bin/env python3
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import requests

app = dash.Dash(__name__)

def get_fpl_data():
    try:
        print("Fetching FPL data...")
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
        data = response.json()
        
        players = pd.DataFrame(data['elements'])
        teams = pd.DataFrame(data['teams'])
        positions = pd.DataFrame(data['element_types'])
        
        team_map = dict(zip(teams['id'], teams['name']))
        pos_map = dict(zip(positions['id'], positions['singular_name']))
        
        players['team_name'] = players['team'].map(team_map)
        players['position'] = players['element_type'].map(pos_map)
        players['price'] = players['now_cost'] / 10
        
        print(f"Loaded {len(players)} players")
        return players
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

# Load data
df = get_fpl_data()

app.layout = html.Div([
    html.H1("FPL Analytics Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Filter by Position:"),
        dcc.Dropdown(
            id='position-dropdown',
            options=[{'label': 'All', 'value': 'all'}] + 
                   [{'label': pos, 'value': pos} for pos in df['position'].unique()] if not df.empty else [],
            value='all'
        )
    ], style={'width': '48%', 'display': 'inline-block'}),
    
    dcc.Graph(id='points-price-graph'),
    
    html.Div(id='player-table')
])

@app.callback(
    [Output('points-price-graph', 'figure'),
     Output('player-table', 'children')],
    [Input('position-dropdown', 'value')]
)
def update_content(position):
    if df.empty:
        return {}, html.P("No data available")
    
    filtered_df = df if position == 'all' else df[df['position'] == position]
    
    # Scatter plot
    fig = px.scatter(filtered_df, x='price', y='total_points', 
                    color='position', hover_data=['web_name'],
                    title="Points vs Price")
    
    # Top players table
    top_players = filtered_df.nlargest(10, 'total_points')[['web_name', 'team_name', 'position', 'price', 'total_points']]
    
    table = dash_table.DataTable(
        data=top_players.to_dict('records'),
        columns=[{"name": i, "id": i} for i in top_players.columns],
        style_cell={'textAlign': 'left'}
    )
    
    return fig, table

if __name__ == '__main__':
    print("Starting app on http://localhost:8052")
    app.run_server(debug=True, port=8052, host='127.0.0.1')