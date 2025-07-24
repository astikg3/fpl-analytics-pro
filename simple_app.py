import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import requests
import dash_bootstrap_components as dbc

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "FPL Analytics Dashboard"

def load_fpl_data():
    """Load and process FPL data"""
    try:
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Create DataFrames
        players_df = pd.DataFrame(data['elements'])
        teams_df = pd.DataFrame(data['teams'])
        positions_df = pd.DataFrame(data['element_types'])
        
        # Create mapping dictionaries
        team_map = dict(zip(teams_df['id'], teams_df['name']))
        position_map = dict(zip(positions_df['id'], positions_df['singular_name']))
        
        # Add mapped columns
        players_df['team_name'] = players_df['team'].map(team_map)
        players_df['position'] = players_df['element_type'].map(position_map)
        players_df['price'] = players_df['now_cost'] / 10
        
        # Filter out unavailable players
        players_df = players_df[players_df['status'] != 'u']
        
        return players_df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data once at startup
print("Loading FPL data...")
players_df = load_fpl_data()
print(f"Loaded {len(players_df)} players")

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🏆 FPL Analytics Dashboard", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📊 Quick Stats"),
                    html.P(f"Total Players: {len(players_df)}"),
                    html.P(f"Teams: {players_df['team_name'].nunique() if not players_df.empty else 0}"),
                    dbc.Button("🔄 Refresh", id="refresh-btn", color="primary", size="sm")
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🎯 Filters"),
                    html.Label("Position:"),
                    dcc.Dropdown(
                        id="position-filter",
                        options=[{"label": "All", "value": "all"}] + 
                               [{"label": pos, "value": pos} for pos in sorted(players_df['position'].unique())] if not players_df.empty else [],
                        value="all"
                    ),
                    html.Br(),
                    html.Label("Max Price (£):"),
                    dcc.Slider(
                        id="price-filter",
                        min=4,
                        max=15,
                        value=15,
                        marks={i: f"£{i}" for i in range(4, 16, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ])
            ])
        ], width=9)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="scatter-plot", style={"height": "400px"})
        ], width=6),
        dbc.Col([
            dcc.Graph(id="bar-chart", style={"height": "400px"})
        ], width=6)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.H5("🏅 Top Players"),
            dash_table.DataTable(
                id="players-table",
                columns=[
                    {"name": "Player", "id": "web_name"},
                    {"name": "Team", "id": "team_name"},
                    {"name": "Position", "id": "position"},
                    {"name": "Price", "id": "price", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "Points", "id": "total_points", "type": "numeric"},
                    {"name": "PPG", "id": "points_per_game", "type": "numeric", "format": {"specifier": ".1f"}}
                ],
                data=[],
                sort_action="native",
                page_size=10,
                style_cell={'textAlign': 'left', 'fontSize': '14px'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
            )
        ])
    ])
], fluid=True)

@app.callback(
    [Output("scatter-plot", "figure"),
     Output("bar-chart", "figure"),
     Output("players-table", "data")],
    [Input("position-filter", "value"),
     Input("price-filter", "value")]
)
def update_dashboard(position, max_price):
    if players_df.empty:
        empty_fig = px.scatter(title="No data available")
        return empty_fig, empty_fig, []
    
    # Filter data
    filtered_df = players_df.copy()
    
    if position != "all":
        filtered_df = filtered_df[filtered_df['position'] == position]
    
    filtered_df = filtered_df[filtered_df['price'] <= max_price]
    
    # Points vs Price scatter
    scatter_fig = px.scatter(
        filtered_df,
        x='price',
        y='total_points',
        color='position',
        hover_data=['web_name', 'team_name'],
        title="💰 Points vs Price Analysis"
    )
    scatter_fig.update_layout(
        xaxis_title="Price (£)",
        yaxis_title="Total Points",
        height=400
    )
    
    # Top performers bar chart
    top_players = filtered_df.nlargest(10, 'total_points')
    bar_fig = px.bar(
        top_players,
        x='total_points',
        y='web_name',
        orientation='h',
        title="🔥 Top 10 Point Scorers",
        color='total_points',
        color_continuous_scale='viridis'
    )
    bar_fig.update_layout(
        xaxis_title="Total Points",
        yaxis_title="",
        yaxis={'categoryorder': 'total ascending'},
        height=400
    )
    
    # Table data
    table_data = filtered_df.nlargest(20, 'total_points')[
        ['web_name', 'team_name', 'position', 'price', 'total_points', 'points_per_game']
    ].to_dict('records')
    
    return scatter_fig, bar_fig, table_data

if __name__ == "__main__":
    print("🚀 Starting FPL Dashboard...")
    print("📱 Open: http://127.0.0.1:8050")
    app.run_server(debug=True, host='127.0.0.1', port=8050)