#!/usr/bin/env python3
"""
Enhanced FPL Analytics Dashboard with Players, Fixtures, and Teams
- Granular fixture difficulty using team strength ratings
- Multi-team fixtures comparison
- Team statistics page
"""
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page config
st.set_page_config(
    page_title="FPL Analytics Pro",
    page_icon="⚽",
    layout="wide"
)

@st.cache_data(ttl=300)
def load_fpl_data():
    """Load FPL data with enhanced metrics"""
    try:
        with st.spinner("Loading FPL data..."):
            # Bootstrap data
            bootstrap_response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=15)
            bootstrap_data = bootstrap_response.json()
            
            # Fixtures data
            fixtures_response = requests.get("https://fantasy.premierleague.com/api/fixtures/", timeout=15)
            fixtures_data = fixtures_response.json()
            
            # Process players data
            players = pd.DataFrame(bootstrap_data['elements'])
            teams = pd.DataFrame(bootstrap_data['teams'])
            positions = pd.DataFrame(bootstrap_data['element_types'])
            
            # Create lookup dictionaries
            team_lookup = dict(zip(teams['id'], teams['name']))
            position_lookup = dict(zip(positions['id'], positions['singular_name']))
            
            # Add human-readable columns to players
            players['Team'] = players['team'].map(team_lookup)
            players['Position'] = players['element_type'].map(position_lookup)
            players['Price'] = players['now_cost'] / 10
            players['Player'] = players['web_name']
            
            # Calculate useful metrics
            players['Value'] = players['total_points'] / players['Price'].replace(0, 1)
            players['PPG'] = pd.to_numeric(players['points_per_game'], errors='coerce').fillna(0)
            players['Ownership'] = pd.to_numeric(players['selected_by_percent'], errors='coerce').fillna(0)
            players['Form'] = pd.to_numeric(players['form'], errors='coerce').fillna(0)
            
            # Ensure numeric columns are properly typed
            numeric_cols = ['total_points', 'goals_scored', 'assists', 'clean_sheets', 'bonus', 
                           'ict_index', 'expected_goals', 'expected_assists', 'minutes', 'starts',
                           'yellow_cards', 'red_cards', 'saves', 'goals_conceded']
            
            for col in numeric_cols:
                if col in players.columns:
                    players[col] = pd.to_numeric(players[col], errors='coerce').fillna(0)
            
            # Process fixtures data with granular difficulty
            fixtures = pd.DataFrame(fixtures_data)
            fixtures['team_h_name'] = fixtures['team_h'].map(team_lookup)
            fixtures['team_a_name'] = fixtures['team_a'].map(team_lookup)
            
            # Add granular difficulty metrics
            fixtures = calculate_granular_difficulty(fixtures, teams)
            
            # Calculate team statistics
            team_stats = calculate_team_stats(players, teams, fixtures)
            
            st.success(f"✅ Loaded {len(players)} players, {len(fixtures)} fixtures, and {len(teams)} teams!")
            return players, fixtures, teams, team_stats, bootstrap_data
            
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

def calculate_granular_difficulty(fixtures_df, teams_df):
    """Calculate granular fixture difficulty using team strength ratings"""
    
    def get_custom_difficulty(team_h_id, team_a_id, venue='home'):
        """Calculate custom difficulty score (0-10 scale)"""
        if pd.isna(team_h_id) or pd.isna(team_a_id):
            return 5.0  # Default neutral difficulty
        
        team_h = teams_df[teams_df['id'] == team_h_id]
        team_a = teams_df[teams_df['id'] == team_a_id]
        
        if team_h.empty or team_a.empty:
            return 5.0
        
        team_h = team_h.iloc[0]
        team_a = team_a.iloc[0]
        
        if venue == 'home':
            # For home team facing away team
            opponent_attack = team_a['strength_attack_away']
            opponent_defence = team_a['strength_defence_away']
            own_attack = team_h['strength_attack_home']
            own_defence = team_h['strength_defence_home']
        else:
            # For away team facing home team
            opponent_attack = team_h['strength_attack_home']
            opponent_defence = team_h['strength_defence_home']
            own_attack = team_a['strength_attack_away']
            own_defence = team_a['strength_defence_away']
        
        # Normalize to 0-10 scale (higher = more difficult)
        # Difficulty increases with opponent strength and decreases with own strength
        attack_difficulty = (opponent_defence - 1000) / 400 * 5 + 2.5  # Scale opponent defence strength
        defence_difficulty = (opponent_attack - 1000) / 400 * 5 + 2.5  # Scale opponent attack strength
        
        # Combined difficulty
        overall_difficulty = (attack_difficulty + defence_difficulty) / 2
        return max(0, min(10, overall_difficulty))  # Clamp to 0-10
    
    # Calculate granular difficulties
    fixtures_df['home_difficulty_granular'] = fixtures_df.apply(
        lambda row: get_custom_difficulty(row['team_h'], row['team_a'], 'home'), axis=1
    )
    fixtures_df['away_difficulty_granular'] = fixtures_df.apply(
        lambda row: get_custom_difficulty(row['team_h'], row['team_a'], 'away'), axis=1
    )
    
    return fixtures_df

def calculate_team_stats(players_df, teams_df, fixtures_df):
    """Calculate comprehensive team statistics"""
    team_stats = []
    
    for _, team in teams_df.iterrows():
        team_players = players_df[players_df['team'] == team['id']]
        
        if team_players.empty:
            continue
        
        # Basic team metrics
        stats = {
            'team_id': team['id'],
            'team_name': team['name'],
            'total_players': len(team_players),
            'total_points': team_players['total_points'].sum(),
            'avg_points_per_player': team_players['total_points'].mean(),
            'total_goals': team_players['goals_scored'].sum(),
            'total_assists': team_players['assists'].sum(),
            'total_clean_sheets': team_players['clean_sheets'].sum(),
            'total_value': team_players['Price'].sum(),
            'avg_ownership': team_players['Ownership'].mean(),
            'avg_form': team_players['Form'].mean(),
            'total_minutes': team_players['minutes'].sum(),
            
            # Advanced metrics
            'strength_overall_home': team['strength_overall_home'],
            'strength_overall_away': team['strength_overall_away'],
            'strength_attack_home': team['strength_attack_home'],
            'strength_attack_away': team['strength_attack_away'],
            'strength_defence_home': team['strength_defence_home'],
            'strength_defence_away': team['strength_defence_away'],
            
            # Top performers
            'top_scorer': team_players.loc[team_players['total_points'].idxmax(), 'Player'] if not team_players.empty else 'N/A',
            'top_scorer_points': team_players['total_points'].max(),
            'most_expensive': team_players.loc[team_players['Price'].idxmax(), 'Player'] if not team_players.empty else 'N/A',
            'most_expensive_price': team_players['Price'].max(),
        }
        
        # Position-specific stats
        for pos in ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']:
            pos_players = team_players[team_players['Position'] == pos]
            stats[f'{pos.lower()}_count'] = len(pos_players)
            stats[f'{pos.lower()}_avg_points'] = pos_players['total_points'].mean() if not pos_players.empty else 0
        
        team_stats.append(stats)
    
    return pd.DataFrame(team_stats)

def create_multi_team_fixtures_table(fixtures_df, teams_df, selected_teams, gameweeks=10):
    """Create a comparison table of fixtures for multiple teams"""
    
    comparison_data = []
    
    for team_id in selected_teams:
        team_name = teams_df[teams_df['id'] == team_id]['name'].iloc[0]
        
        # Get upcoming fixtures for this team
        team_fixtures = fixtures_df[
            ((fixtures_df['team_h'] == team_id) | (fixtures_df['team_a'] == team_id)) &
            (fixtures_df['event'] <= gameweeks)
        ].copy()
        
        if team_fixtures.empty:
            continue
        
        team_fixtures = team_fixtures.sort_values('event')
        
        for _, fixture in team_fixtures.head(gameweeks).iterrows():
            is_home = fixture['team_h'] == team_id
            opponent = fixture['team_a_name'] if is_home else fixture['team_h_name']
            venue = 'H' if is_home else 'A'
            
            # Use granular difficulty
            difficulty = fixture['home_difficulty_granular'] if is_home else fixture['away_difficulty_granular']
            
            comparison_data.append({
                'Team': team_name,
                'GW': fixture['event'],
                'Opponent': opponent,
                'Venue': venue,
                'FPL_Difficulty': fixture['team_h_difficulty'] if is_home else fixture['team_a_difficulty'],
                'Granular_Difficulty': difficulty,
                'Kickoff': fixture['kickoff_time']
            })
    
    return pd.DataFrame(comparison_data)

def players_page():
    """Players analysis page"""
    st.header("📊 Player Statistics")
    
    players_df, _, _, _, _ = load_fpl_data()
    
    if players_df.empty:
        st.error("No player data available")
        return
    
    # Sidebar filters
    st.sidebar.header("🎯 Player Filters")
    
    # Position filter
    positions = st.sidebar.multiselect(
        "Position", 
        options=players_df['Position'].unique(),
        default=players_df['Position'].unique()
    )
    
    # Team filter
    teams = st.sidebar.multiselect(
        "Team",
        options=sorted(players_df['Team'].unique()),
        default=[]
    )
    
    # Price range
    price_min, price_max = st.sidebar.slider(
        "Price Range (£m)",
        min_value=float(players_df['Price'].min()),
        max_value=float(players_df['Price'].max()),
        value=(4.0, 15.0),
        step=0.1
    )
    
    # Points filter
    min_points = st.sidebar.number_input(
        "Minimum Total Points", 
        min_value=0, 
        max_value=int(players_df['total_points'].max()),
        value=0,
        step=10
    )
    
    # Apply filters
    filtered_df = players_df[
        (players_df['Position'].isin(positions)) &
        (players_df['Price'] >= price_min) &
        (players_df['Price'] <= price_max) &
        (players_df['total_points'] >= min_points)
    ]
    
    if teams:
        filtered_df = filtered_df[filtered_df['Team'].isin(teams)]
    
    # Summary stats
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Players", len(filtered_df))
    with col2:
        st.metric("Avg Price", f"£{filtered_df['Price'].mean():.1f}m")
    with col3:
        st.metric("Avg Points", f"{filtered_df['total_points'].mean():.0f}")
    with col4:
        st.metric("Top Score", f"{filtered_df['total_points'].max()}")
    with col5:
        st.metric("Best Value", f"{filtered_df['Value'].max():.1f}")
    
    # Main content tabs
    tab1, tab2 = st.tabs(["📋 Data Table", "📈 Visualizations"])
    
    with tab1:
        st.subheader("Player Statistics Table")
        
        # Column selection
        available_columns = {
            'Player': 'Player Name',
            'Team': 'Team', 
            'Position': 'Position',
            'Price': 'Price (£m)',
            'total_points': 'Total Points',
            'PPG': 'Points Per Game',
            'goals_scored': 'Goals',
            'assists': 'Assists',
            'clean_sheets': 'Clean Sheets',
            'bonus': 'Bonus Points',
            'Ownership': 'Ownership %',
            'Value': 'Value Score',
            'ict_index': 'ICT Index',
            'Form': 'Form',
            'expected_goals': 'Expected Goals',
            'expected_assists': 'Expected Assists',
            'minutes': 'Minutes',
            'starts': 'Starts'
        }
        
        default_cols = ['Player', 'Team', 'Position', 'Price', 'total_points', 'PPG', 'Ownership']
        
        selected_cols = st.multiselect(
            "Select columns:",
            options=list(available_columns.keys()),
            default=default_cols
        )
        
        if selected_cols:
            # Sort options
            col1, col2, col3 = st.columns(3)
            with col1:
                sort_column = st.selectbox("Sort by:", selected_cols, 
                    index=selected_cols.index('total_points') if 'total_points' in selected_cols else 0)
            with col2:
                sort_order = st.selectbox("Order:", ["Descending", "Ascending"])
            with col3:
                rows_per_page = st.selectbox("Rows per page:", [10, 20, 50, 100], index=1)
            
            # Apply sorting
            ascending = sort_order == "Ascending"
            display_df = filtered_df[selected_cols].sort_values(sort_column, ascending=ascending)
            
            # Format for display
            formatted_df = display_df.copy()
            if 'Price' in formatted_df.columns:
                formatted_df['Price'] = formatted_df['Price'].apply(lambda x: f"£{x:.1f}m")
            if 'PPG' in formatted_df.columns:
                formatted_df['PPG'] = formatted_df['PPG'].apply(lambda x: f"{x:.1f}")
            if 'Value' in formatted_df.columns:
                formatted_df['Value'] = formatted_df['Value'].apply(lambda x: f"{x:.1f}")
            if 'Ownership' in formatted_df.columns:
                formatted_df['Ownership'] = formatted_df['Ownership'].apply(lambda x: f"{x:.1f}%")
            
            # Pagination
            total_rows = len(formatted_df)
            total_pages = (total_rows - 1) // rows_per_page + 1
            
            if total_pages > 1:
                page = st.selectbox(f"Page (of {total_pages}):", range(1, total_pages + 1))
                start_idx = (page - 1) * rows_per_page
                end_idx = start_idx + rows_per_page
                display_formatted = formatted_df.iloc[start_idx:end_idx]
            else:
                display_formatted = formatted_df
            
            st.dataframe(display_formatted, use_container_width=True, height=600)
            
            # Download
            csv = display_df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, f"fpl_players_{len(filtered_df)}_results.csv", "text/csv")
    
    with tab2:
        if len(filtered_df) == 0:
            st.warning("No players match your filters")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top performers
            top_n = st.slider("Show top N players:", 5, min(20, len(filtered_df)), 10)
            top_players = filtered_df.nlargest(top_n, 'total_points')
            
            fig = px.bar(top_players, x='total_points', y='Player', orientation='h',
                        title=f"Top {top_n} Point Scorers", color='total_points',
                        color_continuous_scale='viridis')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Price vs Points
            fig2 = px.scatter(filtered_df, x='Price', y='total_points', color='Position',
                            size='Ownership', hover_data=['Player', 'Team'],
                            title="Price vs Total Points")
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)

def fixtures_page():
    """Enhanced fixtures analysis page"""
    st.header("🗓️ Fixture Difficulty Analysis")
    
    _, fixtures_df, teams_df, _, _ = load_fpl_data()
    
    if fixtures_df.empty or teams_df.empty:
        st.error("No fixtures data available")
        return
    
    # Sidebar filters
    st.sidebar.header("🎯 Fixture Filters")
    
    # Analysis type
    analysis_type = st.sidebar.radio(
        "Analysis Type:",
        ["Single Team", "Multi-Team Comparison"]
    )
    
    if analysis_type == "Single Team":
        # Single team analysis
        team_options = [(row['name'], row['id']) for _, row in teams_df.iterrows()]
        team_names = [name for name, _ in team_options]
        selected_team_name = st.sidebar.selectbox("Select Team:", team_names)
        selected_team_id = next(team_id for name, team_id in team_options if name == selected_team_name)
        
        # Rolling window
        window = st.sidebar.slider("Rolling Window (Gameweeks):", 1, 10, 5)
        
        # Single team analysis (existing code)
        single_team_analysis(fixtures_df, teams_df, selected_team_id, selected_team_name, window)
        
    else:
        # Multi-team comparison
        team_names = [row['name'] for _, row in teams_df.iterrows()]
        selected_teams = st.sidebar.multiselect(
            "Select Teams to Compare:",
            options=team_names,
            default=team_names[:4]  # Default to first 4 teams
        )
        
        gameweeks = st.sidebar.slider("Next N Gameweeks:", 5, 20, 10)
        
        if selected_teams:
            multi_team_analysis(fixtures_df, teams_df, selected_teams, gameweeks)

def single_team_analysis(fixtures_df, teams_df, team_id, team_name, window):
    """Single team fixture analysis"""
    # Get team fixtures
    team_fixtures = fixtures_df[
        (fixtures_df['team_h'] == team_id) | (fixtures_df['team_a'] == team_id)
    ].copy()
    
    if team_fixtures.empty:
        st.warning(f"No fixture data available for {team_name}")
        return
    
    team_fixtures = team_fixtures.sort_values('event')
    
    # Add difficulty and opponent info
    team_fixtures['difficulty'] = team_fixtures.apply(
        lambda row: row['home_difficulty_granular'] if row['team_h'] == team_id else row['away_difficulty_granular'],
        axis=1
    )
    team_fixtures['venue'] = team_fixtures.apply(
        lambda row: 'Home' if row['team_h'] == team_id else 'Away', axis=1
    )
    team_fixtures['opponent'] = team_fixtures.apply(
        lambda row: row['team_a_name'] if row['team_h'] == team_id else row['team_h_name'], axis=1
    )
    
    # Calculate rolling average
    team_fixtures['rolling_difficulty'] = team_fixtures['difficulty'].rolling(window=window, min_periods=1).mean()
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fixtures", len(team_fixtures))
    with col2:
        st.metric("Avg Difficulty", f"{team_fixtures['difficulty'].mean():.2f}")
    with col3:
        next_5_avg = team_fixtures.head(5)['difficulty'].mean() if len(team_fixtures) >= 5 else team_fixtures['difficulty'].mean()
        st.metric("Next 5 GWs", f"{next_5_avg:.2f}")
    with col4:
        st.metric(f"Rolling {window}-GW", f"{team_fixtures['rolling_difficulty'].iloc[-1]:.2f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Trend chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=team_fixtures['event'], y=team_fixtures['difficulty'],
            mode='markers', name='Granular Difficulty (0-10)',
            marker=dict(size=8, opacity=0.7),
            hovertemplate='<b>GW %{x}</b><br>Difficulty: %{y:.2f}<br>Opponent: %{customdata}<extra></extra>',
            customdata=team_fixtures['opponent']
        ))
        fig.add_trace(go.Scatter(
            x=team_fixtures['event'], y=team_fixtures['rolling_difficulty'],
            mode='lines+markers', name=f'{window}-GW Rolling Average',
            line=dict(width=3, color='red')
        ))
        fig.update_layout(title=f"{team_name} - Fixture Difficulty Trend",
                         xaxis_title="Gameweek", yaxis_title="Difficulty (0=Easy, 10=Hard)",
                         height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Difficulty distribution
        difficulty_counts = team_fixtures['difficulty'].round().value_counts().sort_index()
        fig2 = px.bar(x=difficulty_counts.index, y=difficulty_counts.values,
                     title="Difficulty Distribution", labels={'x': 'Difficulty Level', 'y': 'Count'})
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Fixtures table
    st.subheader("Upcoming Fixtures")
    upcoming = team_fixtures.head(15)[['event', 'opponent', 'venue', 'difficulty']].copy()
    upcoming.columns = ['GW', 'Opponent', 'Venue', 'Difficulty']
    upcoming['Difficulty'] = upcoming['Difficulty'].round(2)
    st.dataframe(upcoming, use_container_width=True)

def multi_team_analysis(fixtures_df, teams_df, selected_teams, gameweeks):
    """Multi-team fixtures comparison"""
    
    # Get team IDs
    team_id_map = dict(zip(teams_df['name'], teams_df['id']))
    selected_team_ids = [team_id_map[name] for name in selected_teams if name in team_id_map]
    
    # Create comparison table
    comparison_df = create_multi_team_fixtures_table(fixtures_df, teams_df, selected_team_ids, gameweeks)
    
    if comparison_df.empty:
        st.warning("No fixture data available for selected teams")
        return
    
    # Summary statistics
    st.subheader("Team Difficulty Summary")
    summary_stats = comparison_df.groupby('Team').agg({
        'Granular_Difficulty': ['mean', 'min', 'max', 'count']
    }).round(2)
    summary_stats.columns = ['Avg Difficulty', 'Min Difficulty', 'Max Difficulty', 'Fixtures']
    summary_stats = summary_stats.sort_values('Avg Difficulty')
    st.dataframe(summary_stats, use_container_width=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Average difficulty comparison
        avg_difficulty = comparison_df.groupby('Team')['Granular_Difficulty'].mean().sort_values()
        fig1 = px.bar(x=avg_difficulty.values, y=avg_difficulty.index, orientation='h',
                     title="Average Fixture Difficulty by Team", color=avg_difficulty.values,
                     color_continuous_scale='RdYlGn_r')
        fig1.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Difficulty over time
        fig2 = px.line(comparison_df, x='GW', y='Granular_Difficulty', color='Team',
                      title="Difficulty Trends Over Gameweeks", markers=True)
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed comparison table
    st.subheader("Detailed Fixtures Comparison")
    
    # Format display
    display_df = comparison_df.copy()
    display_df['Granular_Difficulty'] = display_df['Granular_Difficulty'].round(2)
    display_df = display_df.sort_values(['GW', 'Team'])
    
    # Color coding for difficulty
    def color_difficulty(val):
        if val >= 7:
            return 'background-color: #ffcdd2'  # Light red
        elif val >= 5.5:
            return 'background-color: #fff3e0'  # Light orange
        elif val >= 4:
            return 'background-color: #fff9c4'  # Light yellow
        elif val >= 2.5:
            return 'background-color: #c8e6c9'  # Light green
        else:
            return 'background-color: #e8f5e8'  # Very light green
    
    styled_df = display_df.style.map(color_difficulty, subset=['Granular_Difficulty'])
    st.dataframe(styled_df, use_container_width=True, height=600)
    
    # Download
    csv = display_df.to_csv(index=False)
    st.download_button("📥 Download Comparison CSV", csv, f"fpl_fixtures_comparison_{gameweeks}gw.csv", "text/csv")

def teams_page():
    """Team statistics page"""
    st.header("🏟️ Team Statistics")
    
    _, _, teams_df, team_stats_df, _ = load_fpl_data()
    
    if team_stats_df.empty:
        st.error("No team data available")
        return
    
    # Sidebar filters
    st.sidebar.header("🎯 Team Filters")
    
    selected_teams = st.sidebar.multiselect(
        "Select Teams:",
        options=team_stats_df['team_name'].tolist(),
        default=team_stats_df['team_name'].tolist()
    )
    
    if not selected_teams:
        st.warning("Please select at least one team")
        return
    
    filtered_teams = team_stats_df[team_stats_df['team_name'].isin(selected_teams)]
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Teams", len(filtered_teams))
    with col2:
        st.metric("Total Points", f"{filtered_teams['total_points'].sum():,}")
    with col3:
        st.metric("Total Goals", f"{filtered_teams['total_goals'].sum()}")
    with col4:
        st.metric("Total Assists", f"{filtered_teams['total_assists'].sum()}")
    with col5:
        st.metric("Avg Team Value", f"£{filtered_teams['total_value'].mean():.1f}m")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📋 Team Stats Table", "📊 Performance Analysis", "⚡ Strength Ratings"])
    
    with tab1:
        st.subheader("Team Statistics Table")
        
        # Column selection
        available_columns = {
            'team_name': 'Team',
            'total_points': 'Total Points',
            'avg_points_per_player': 'Avg Points/Player',
            'total_goals': 'Goals',
            'total_assists': 'Assists',
            'total_clean_sheets': 'Clean Sheets',
            'total_value': 'Total Value (£m)',
            'avg_ownership': 'Avg Ownership %',
            'avg_form': 'Avg Form',
            'top_scorer': 'Top Scorer',
            'top_scorer_points': 'Top Scorer Points',
            'most_expensive': 'Most Expensive Player',
            'most_expensive_price': 'Highest Price (£m)'
        }
        
        default_cols = ['team_name', 'total_points', 'avg_points_per_player', 'total_goals', 'total_assists', 'avg_ownership']
        
        selected_cols = st.multiselect(
            "Select columns:",
            options=list(available_columns.keys()),
            default=default_cols
        )
        
        if selected_cols:
            # Sort options
            col1, col2 = st.columns(2)
            with col1:
                sort_column = st.selectbox("Sort by:", selected_cols,
                    index=selected_cols.index('total_points') if 'total_points' in selected_cols else 0)
            with col2:
                sort_order = st.selectbox("Order:", ["Descending", "Ascending"])
            
            # Apply sorting
            ascending = sort_order == "Ascending"
            display_df = filtered_teams[selected_cols].sort_values(sort_column, ascending=ascending)
            
            # Format for display
            formatted_df = display_df.copy()
            if 'total_value' in formatted_df.columns:
                formatted_df['total_value'] = formatted_df['total_value'].apply(lambda x: f"£{x:.1f}m")
            if 'avg_ownership' in formatted_df.columns:
                formatted_df['avg_ownership'] = formatted_df['avg_ownership'].apply(lambda x: f"{x:.1f}%")
            if 'avg_form' in formatted_df.columns:
                formatted_df['avg_form'] = formatted_df['avg_form'].apply(lambda x: f"{x:.1f}")
            if 'most_expensive_price' in formatted_df.columns:
                formatted_df['most_expensive_price'] = formatted_df['most_expensive_price'].apply(lambda x: f"£{x:.1f}m")
            
            st.dataframe(formatted_df, use_container_width=True, height=600)
            
            # Download
            csv = display_df.to_csv(index=False)
            st.download_button("📥 Download Team Stats CSV", csv, f"fpl_team_stats_{len(filtered_teams)}_teams.csv", "text/csv")
    
    with tab2:
        st.subheader("Team Performance Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Total points comparison
            fig1 = px.bar(filtered_teams.sort_values('total_points', ascending=True),
                         x='total_points', y='team_name', orientation='h',
                         title="Total Points by Team", color='total_points',
                         color_continuous_scale='viridis')
            fig1.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Goals vs Assists
            fig2 = px.scatter(filtered_teams, x='total_goals', y='total_assists',
                            size='total_points', color='avg_ownership',
                            hover_data=['team_name'], title="Goals vs Assists")
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Value vs Performance
            fig3 = px.scatter(filtered_teams, x='total_value', y='total_points',
                            color='team_name', title="Team Value vs Points",
                            hover_data=['avg_points_per_player'])
            fig3.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
        
        with col4:
            # Average ownership distribution
            fig4 = px.bar(filtered_teams.sort_values('avg_ownership', ascending=True),
                         x='avg_ownership', y='team_name', orientation='h',
                         title="Average Player Ownership %", color='avg_ownership',
                         color_continuous_scale='blues')
            fig4.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig4, use_container_width=True)
    
    with tab3:
        st.subheader("Team Strength Ratings")
        
        # Strength metrics comparison
        strength_cols = ['strength_overall_home', 'strength_overall_away', 
                        'strength_attack_home', 'strength_attack_away',
                        'strength_defence_home', 'strength_defence_away']
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Home vs Away overall strength
            fig1 = px.scatter(filtered_teams, x='strength_overall_home', y='strength_overall_away',
                            color='team_name', title="Home vs Away Overall Strength",
                            hover_data=['team_name'])
            fig1.add_shape(type="line", line=dict(dash="dash"), 
                          x0=filtered_teams['strength_overall_home'].min(),
                          x1=filtered_teams['strength_overall_home'].max(),
                          y0=filtered_teams['strength_overall_away'].min(),
                          y1=filtered_teams['strength_overall_away'].max())
            fig1.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            # Attack vs Defence strength (average)
            filtered_teams['avg_attack'] = (filtered_teams['strength_attack_home'] + filtered_teams['strength_attack_away']) / 2
            filtered_teams['avg_defence'] = (filtered_teams['strength_defence_home'] + filtered_teams['strength_defence_away']) / 2
            
            fig2 = px.scatter(filtered_teams, x='avg_attack', y='avg_defence',
                            color='team_name', title="Attack vs Defence Strength",
                            hover_data=['team_name'])
            fig2.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Strength ratings table
        st.subheader("Detailed Strength Ratings")
        strength_display = filtered_teams[['team_name'] + strength_cols].copy()
        strength_display = strength_display.sort_values('strength_overall_home', ascending=False)
        st.dataframe(strength_display, use_container_width=True)

def main():
    st.title("⚽ FPL Analytics Pro")
    st.markdown("### Enhanced Fantasy Premier League Analysis with Granular Data")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["📊 Player Statistics", "🗓️ Fixture Analysis", "🏟️ Team Statistics"]
    )
    
    if page == "📊 Player Statistics":
        players_page()
    elif page == "🗓️ Fixture Analysis":
        fixtures_page()
    elif page == "🏟️ Team Statistics":
        teams_page()

if __name__ == "__main__":
    main()