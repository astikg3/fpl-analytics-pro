#!/usr/bin/env python3
import dash
from dash import dcc, html, Input, Output, dash_table, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import numpy as np
from datetime import datetime
import dash_bootstrap_components as dbc

# Initialize app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

class FPLData:
    def __init__(self):
        self.bootstrap_data = None
        self.fixtures_data = None
        self.load_data()
    
    def load_data(self):
        try:
            print("Loading FPL data...")
            # Bootstrap data
            response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
            self.bootstrap_data = response.json()
            
            # Fixtures data
            response = requests.get("https://fantasy.premierleague.com/api/fixtures/", timeout=10)
            self.fixtures_data = response.json()
            
            print(f"Loaded {len(self.bootstrap_data['elements'])} players and {len(self.fixtures_data)} fixtures")
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def get_players_df(self):
        if not self.bootstrap_data:
            return pd.DataFrame()
        
        players = pd.DataFrame(self.bootstrap_data['elements'])
        teams = pd.DataFrame(self.bootstrap_data['teams'])
        positions = pd.DataFrame(self.bootstrap_data['element_types'])
        
        team_map = dict(zip(teams['id'], teams['name']))
        pos_map = dict(zip(positions['id'], positions['singular_name']))
        
        players['team_name'] = players['team'].map(team_map)
        players['position'] = players['element_type'].map(pos_map)
        players['price'] = players['now_cost'] / 10
        
        return players
    
    def get_fixtures_df(self):
        if not self.fixtures_data:
            return pd.DataFrame()
        
        fixtures = pd.DataFrame(self.fixtures_data)
        teams = pd.DataFrame(self.bootstrap_data['teams'])
        team_map = dict(zip(teams['id'], teams['name']))
        
        fixtures['team_h_name'] = fixtures['team_h'].map(team_map)
        fixtures['team_a_name'] = fixtures['team_a'].map(team_map)
        
        return fixtures
    
    def calculate_fixture_difficulty(self, team_id, window=5):
        """Calculate rolling fixture difficulty for a team"""
        fixtures = self.get_fixtures_df()
        
        # Get fixtures for this team (home and away)
        team_fixtures = fixtures[
            (fixtures['team_h'] == team_id) | (fixtures['team_a'] == team_id)
        ].copy()
        
        # Sort by gameweek
        team_fixtures = team_fixtures.sort_values('event')
        
        # Calculate difficulty (team_h_difficulty for home, team_a_difficulty for away)
        team_fixtures['difficulty'] = team_fixtures.apply(
            lambda row: row['team_h_difficulty'] if row['team_h'] == team_id else row['team_a_difficulty'],
            axis=1
        )
        
        # Calculate rolling average
        team_fixtures['rolling_difficulty'] = team_fixtures['difficulty'].rolling(
            window=window, min_periods=1
        ).mean()
        
        return team_fixtures[['event', 'difficulty', 'rolling_difficulty', 'team_h_name', 'team_a_name']]

# Initialize data
fpl_data = FPLData()

# App layout with navigation
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    
    # Navigation
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Players", href="/", active="exact")),
            dbc.NavItem(dbc.NavLink("Fixture Difficulty", href="/fixtures", active="exact")),
        ],
        brand="🏆 FPL Analytics Dashboard",
        brand_href="/",
        color="primary",
        dark=True,
        className="mb-4"
    ),
    
    # Page content
    html.Div(id='page-content')
], fluid=True)

# Page layouts
def players_layout():
    df = fpl_data.get_players_df()
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Quick Stats"),
                        html.P(f"Total Players: {len(df)}"),
                        html.P(f"Teams: {df['team_name'].nunique() if not df.empty else 0}"),
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
                                   [{"label": pos, "value": pos} for pos in sorted(df['position'].unique())] if not df.empty else [],
                            value="all"
                        ),
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
                    ],
                    data=[],
                    sort_action="native",
                    page_size=10,
                    style_cell={'textAlign': 'left', 'fontSize': '14px'},
                    style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
                )
            ])
        ])
    ])

def fixtures_layout():
    teams_df = pd.DataFrame(fpl_data.bootstrap_data['teams']) if fpl_data.bootstrap_data else pd.DataFrame()
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("🗓️ Fixture Difficulty Analysis"),
                        html.P("Analyze team fixture difficulty over time with rolling averages"),
                    ])
                ])
            ])
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("⚙️ Settings"),
                        html.Label("Select Team:"),
                        dcc.Dropdown(
                            id="team-selector",
                            options=[{"label": team['name'], "value": team['id']} 
                                   for team in teams_df.to_dict('records')] if not teams_df.empty else [],
                            value=1,  # Arsenal by default
                            placeholder="Choose a team"
                        ),
                        html.Br(),
                        html.Label("Rolling Window (Gameweeks):"),
                        dcc.Slider(
                            id="window-slider",
                            min=1,
                            max=10,
                            value=5,
                            marks={i: str(i) for i in range(1, 11)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                    ])
                ])
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📈 Difficulty Summary"),
                        html.Div(id="difficulty-summary")
                    ])
                ])
            ], width=8)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dcc.Graph(id="difficulty-trend", style={"height": "500px"})
            ], width=12)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.H5("📋 Upcoming Fixtures"),
                dash_table.DataTable(
                    id="fixtures-table",
                    columns=[
                        {"name": "GW", "id": "event"},
                        {"name": "Opponent", "id": "opponent"},
                        {"name": "Home/Away", "id": "venue"},
                        {"name": "Difficulty", "id": "difficulty"},
                    ],
                    data=[],
                    sort_action="native",
                    page_size=10,
                    style_cell={'textAlign': 'left'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{difficulty} = 5'},
                            'backgroundColor': '#ffebee',
                            'color': 'black',
                        },
                        {
                            'if': {'filter_query': '{difficulty} = 4'},
                            'backgroundColor': '#fff3e0',
                            'color': 'black',
                        },
                        {
                            'if': {'filter_query': '{difficulty} = 2'},
                            'backgroundColor': '#e8f5e8',
                            'color': 'black',
                        }
                    ]
                )
            ])
        ])
    ])

# Callbacks for navigation
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/fixtures':
        return fixtures_layout()
    else:
        return players_layout()

# Players page callbacks
@app.callback(
    [Output("scatter-plot", "figure"),
     Output("bar-chart", "figure"),
     Output("players-table", "data")],
    [Input("position-filter", "value")]
)
def update_players_page(position):
    df = fpl_data.get_players_df()
    
    if df.empty:
        empty_fig = px.scatter(title="No data available")
        return empty_fig, empty_fig, []
    
    # Filter data
    filtered_df = df if position == "all" else df[df['position'] == position]
    
    # Scatter plot
    scatter_fig = px.scatter(
        filtered_df,
        x='price',
        y='total_points',
        color='position',
        hover_data=['web_name', 'team_name'],
        title="💰 Points vs Price Analysis"
    )
    
    # Bar chart
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
    bar_fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    
    # Table data
    table_data = filtered_df.nlargest(20, 'total_points')[
        ['web_name', 'team_name', 'position', 'price', 'total_points']
    ].to_dict('records')
    
    return scatter_fig, bar_fig, table_data

# Fixtures page callbacks
@app.callback(
    [Output("difficulty-trend", "figure"),
     Output("difficulty-summary", "children"),
     Output("fixtures-table", "data")],
    [Input("team-selector", "value"),
     Input("window-slider", "value")]
)
def update_fixtures_page(team_id, window):
    if not team_id:
        empty_fig = px.line(title="Select a team to view fixture difficulty")
        return empty_fig, "Select a team", []
    
    # Get team difficulty data
    difficulty_data = fpl_data.calculate_fixture_difficulty(team_id, window)
    
    if difficulty_data.empty:
        empty_fig = px.line(title="No fixture data available")
        return empty_fig, "No data", []
    
    # Get team name
    teams_df = pd.DataFrame(fpl_data.bootstrap_data['teams'])
    team_name = teams_df[teams_df['id'] == team_id]['name'].iloc[0]
    
    # Create trend chart
    fig = go.Figure()
    
    # Add raw difficulty
    fig.add_trace(go.Scatter(
        x=difficulty_data['event'],
        y=difficulty_data['difficulty'],
        mode='markers',
        name='Fixture Difficulty',
        marker=dict(size=8, opacity=0.6),
        hovertemplate='GW %{x}<br>Difficulty: %{y}<extra></extra>'
    ))
    
    # Add rolling average
    fig.add_trace(go.Scatter(
        x=difficulty_data['event'],
        y=difficulty_data['rolling_difficulty'],
        mode='lines+markers',
        name=f'{window}-GW Rolling Average',
        line=dict(width=3),
        hovertemplate='GW %{x}<br>Rolling Avg: %{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"🗓️ {team_name} - Fixture Difficulty Trend",
        xaxis_title="Gameweek",
        yaxis_title="Difficulty (1=Easy, 5=Hard)",
        yaxis=dict(range=[1, 5]),
        height=500,
        hovermode='x unified'
    )
    
    # Summary stats
    avg_difficulty = difficulty_data['difficulty'].mean()
    next_5_avg = difficulty_data.head(5)['difficulty'].mean() if len(difficulty_data) >= 5 else avg_difficulty
    
    summary = dbc.Row([
        dbc.Col([
            html.H6("Overall Average"),
            html.H4(f"{avg_difficulty:.2f}", className="text-primary")
        ], width=4),
        dbc.Col([
            html.H6("Next 5 GWs Average"),
            html.H4(f"{next_5_avg:.2f}", className="text-warning")
        ], width=4),
        dbc.Col([
            html.H6(f"Rolling {window}-GW Average"),
            html.H4(f"{difficulty_data['rolling_difficulty'].iloc[-1]:.2f}", className="text-success")
        ], width=4)
    ])
    
    # Fixtures table
    upcoming_fixtures = difficulty_data.head(10).copy()
    upcoming_fixtures['opponent'] = upcoming_fixtures.apply(
        lambda row: row['team_a_name'] if row['team_h_name'] == team_name else row['team_h_name'],
        axis=1
    )
    upcoming_fixtures['venue'] = upcoming_fixtures.apply(
        lambda row: 'Home' if row['team_h_name'] == team_name else 'Away',
        axis=1
    )
    
    table_data = upcoming_fixtures[['event', 'opponent', 'venue', 'difficulty']].to_dict('records')
    
    return fig, summary, table_data

if __name__ == '__main__':
    print("🚀 Starting Multi-Page FPL Dashboard...")
    print("📱 Players: http://127.0.0.1:8053")
    print("🗓️  Fixtures: http://127.0.0.1:8053/fixtures")
    app.run_server(debug=True, port=8053, host='127.0.0.1')