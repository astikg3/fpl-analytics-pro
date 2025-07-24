import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
from src.data_scraper import FPLDataScraper

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "FPL Analytics Dashboard"

# Initialize data scraper
scraper = FPLDataScraper()

# Load initial data
try:
    players_df = scraper.get_player_data()
    print(f"Loaded {len(players_df)} players successfully")
except Exception as e:
    print(f"Error loading data: {e}")
    players_df = pd.DataFrame(columns=['position', 'team_name', 'now_cost', 'total_points', 'web_name', 'points_per_game'])

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Fantasy Premier League Analytics", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Data Overview", className="card-title"),
                    html.P(f"Total Players: {len(players_df)}", id="total-players"),
                    dbc.Button("Refresh Data", id="refresh-btn", color="primary", className="mb-2"),
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Filters", className="card-title"),
                    html.Label("Position:"),
                    dcc.Dropdown(
                        id="position-dropdown",
                        options=[{"label": pos, "value": pos} 
                                for pos in players_df['position'].unique()] if not players_df.empty else [],
                        value=None,
                        placeholder="Select position"
                    ),
                    html.Br(),
                    html.Label("Team:"),
                    dcc.Dropdown(
                        id="team-dropdown",
                        options=[{"label": team, "value": team} 
                                for team in players_df['team_name'].unique()] if not players_df.empty else [],
                        value=None,
                        placeholder="Select team"
                    ),
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Price Range", className="card-title"),
                    dcc.RangeSlider(
                        id="price-slider",
                        min=players_df['now_cost'].min()/10 if not players_df.empty else 0,
                        max=players_df['now_cost'].max()/10 if not players_df.empty else 15,
                        value=[4.0, 15.0],
                        marks={i: f"£{i}m" for i in range(4, 16, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ])
            ])
        ], width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="points-vs-price-scatter")
        ], width=6),
        dbc.Col([
            dcc.Graph(id="top-scorers-bar")
        ], width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="team-performance-bar")
        ], width=6),
        dbc.Col([
            dcc.Graph(id="position-distribution-pie")
        ], width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.H4("Player Data Table"),
            dash_table.DataTable(
                id="players-table",
                columns=[
                    {"name": "Name", "id": "web_name"},
                    {"name": "Team", "id": "team_name"},
                    {"name": "Position", "id": "position"},
                    {"name": "Price (£m)", "id": "price", "type": "numeric", "format": {"specifier": ".1f"}},
                    {"name": "Total Points", "id": "total_points"},
                    {"name": "PPG", "id": "points_per_game", "type": "numeric", "format": {"specifier": ".1f"}},
                ],
                data=[],
                sort_action="native",
                page_size=15,
                style_cell={'textAlign': 'left'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ]
            )
        ])
    ])
], fluid=True)

# Callbacks
@app.callback(
    [Output("points-vs-price-scatter", "figure"),
     Output("top-scorers-bar", "figure"),
     Output("team-performance-bar", "figure"),
     Output("position-distribution-pie", "figure"),
     Output("players-table", "data")],
    [Input("position-dropdown", "value"),
     Input("team-dropdown", "value"),
     Input("price-slider", "value"),
     Input("refresh-btn", "n_clicks")]
)
def update_dashboard(position, team, price_range, n_clicks):
    # Filter data based on selections
    filtered_df = players_df.copy()
    
    if position:
        filtered_df = filtered_df[filtered_df['position'] == position]
    if team:
        filtered_df = filtered_df[filtered_df['team_name'] == team]
    if price_range:
        min_price, max_price = price_range
        filtered_df = filtered_df[
            (filtered_df['now_cost']/10 >= min_price) & 
            (filtered_df['now_cost']/10 <= max_price)
        ]
    
    # Add price column for display
    filtered_df['price'] = filtered_df['now_cost'] / 10
    
    # Points vs Price scatter plot
    scatter_fig = px.scatter(
        filtered_df, 
        x='price', 
        y='total_points',
        color='position',
        hover_data=['web_name', 'team_name'],
        title="Points vs Price"
    )
    scatter_fig.update_layout(xaxis_title="Price (£m)", yaxis_title="Total Points")
    
    # Top scorers bar chart
    top_scorers = filtered_df.nlargest(10, 'total_points')
    bar_fig = px.bar(
        top_scorers,
        x='total_points',
        y='web_name',
        orientation='h',
        title="Top 10 Scorers",
        color='total_points',
        color_continuous_scale='viridis'
    )
    bar_fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    
    # Team performance
    team_stats = filtered_df.groupby('team_name')['total_points'].mean().reset_index()
    team_fig = px.bar(
        team_stats.sort_values('total_points', ascending=False).head(10),
        x='team_name',
        y='total_points',
        title="Average Points by Team (Top 10)"
    )
    team_fig.update_layout(xaxis_title="Team", yaxis_title="Average Points")
    
    # Position distribution
    position_counts = filtered_df['position'].value_counts()
    pie_fig = px.pie(
        values=position_counts.values,
        names=position_counts.index,
        title="Player Distribution by Position"
    )
    
    # Table data
    table_data = filtered_df[['web_name', 'team_name', 'position', 'price', 'total_points', 'points_per_game']].to_dict('records')
    
    return scatter_fig, bar_fig, team_fig, pie_fig, table_data

if __name__ == "__main__":
    app.run_server(debug=True)