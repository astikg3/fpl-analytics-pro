#!/usr/bin/env python3
"""
Complete FPL Analytics Dashboard with Players and Fixtures
"""
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page config
st.set_page_config(
    page_title="FPL Analytics Dashboard",
    page_icon="⚽",
    layout="wide"
)

@st.cache_data(ttl=300)
def load_fpl_data():
    """Load FPL data with error handling"""
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
            
            # Calculate useful metrics - handle missing values
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
            
            # Process fixtures data
            fixtures = pd.DataFrame(fixtures_data)
            fixtures['team_h_name'] = fixtures['team_h'].map(team_lookup)
            fixtures['team_a_name'] = fixtures['team_a'].map(team_lookup)
            
            st.success(f"✅ Loaded {len(players)} players and {len(fixtures)} fixtures!")
            return players, fixtures, teams, bootstrap_data
            
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

def calculate_fixture_difficulty(fixtures_df, team_id, window=5):
    """Calculate rolling fixture difficulty for a team"""
    if fixtures_df.empty:
        return pd.DataFrame()
    
    # Get fixtures for this team (home and away)
    team_fixtures = fixtures_df[
        (fixtures_df['team_h'] == team_id) | (fixtures_df['team_a'] == team_id)
    ].copy()
    
    if team_fixtures.empty:
        return pd.DataFrame()
    
    # Sort by gameweek
    team_fixtures = team_fixtures.sort_values('event')
    
    # Calculate difficulty (team_h_difficulty for home, team_a_difficulty for away)
    team_fixtures['difficulty'] = team_fixtures.apply(
        lambda row: row['team_h_difficulty'] if row['team_h'] == team_id else row['team_a_difficulty'],
        axis=1
    )
    
    # Add venue information
    team_fixtures['venue'] = team_fixtures.apply(
        lambda row: 'Home' if row['team_h'] == team_id else 'Away',
        axis=1
    )
    
    # Add opponent information
    team_fixtures['opponent'] = team_fixtures.apply(
        lambda row: row['team_a_name'] if row['team_h'] == team_id else row['team_h_name'],
        axis=1
    )
    
    # Calculate rolling average
    team_fixtures['rolling_difficulty'] = team_fixtures['difficulty'].rolling(
        window=window, min_periods=1
    ).mean()
    
    return team_fixtures[['event', 'difficulty', 'rolling_difficulty', 'venue', 'opponent', 'kickoff_time']]

def players_page():
    """Players analysis page"""
    st.header("📊 Player Statistics")
    
    players_df, _, _, _ = load_fpl_data()
    
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
    
    # Ownership filter
    min_ownership = st.sidebar.slider(
        "Minimum Ownership %",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.5
    )
    
    # Apply filters
    filtered_df = players_df[
        (players_df['Position'].isin(positions)) &
        (players_df['Price'] >= price_min) &
        (players_df['Price'] <= price_max) &
        (players_df['total_points'] >= min_points) &
        (players_df['Ownership'] >= min_ownership)
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
    tab1, tab2, tab3 = st.tabs(["📋 Data Table", "📈 Visualizations", "🔍 Player Details"])
    
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
            'starts': 'Starts',
            'yellow_cards': 'Yellow Cards',
            'red_cards': 'Red Cards'
        }
        
        # Default columns
        default_cols = ['Player', 'Team', 'Position', 'Price', 'total_points', 'PPG', 'Ownership']
        
        selected_cols = st.multiselect(
            "Select columns to display:",
            options=list(available_columns.keys()),
            default=default_cols
        )
        
        if not selected_cols:
            st.warning("Please select at least one column to display")
            return
        
        # Sort options
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_column = st.selectbox(
                "Sort by:",
                options=selected_cols,
                index=selected_cols.index('total_points') if 'total_points' in selected_cols else 0
            )
        with col2:
            sort_order = st.selectbox("Order:", ["Descending", "Ascending"])
        with col3:
            rows_per_page = st.selectbox("Rows per page:", [10, 20, 50, 100], index=1)
        
        # Apply sorting - fix the sorting issue
        ascending = sort_order == "Ascending"
        
        # Make sure we're sorting by the raw numeric values, not formatted strings
        if sort_column in ['Price', 'PPG', 'Ownership', 'Value', 'Form']:
            # Use the original numeric columns for sorting
            sort_map = {
                'Price': 'Price',
                'PPG': 'PPG', 
                'Ownership': 'Ownership',
                'Value': 'Value',
                'Form': 'Form'
            }
            actual_sort_col = sort_map.get(sort_column, sort_column)
        else:
            actual_sort_col = sort_column
        
        display_df = filtered_df[selected_cols].sort_values(actual_sort_col, ascending=ascending)
        
        # Format for display (but keep original for sorting)
        formatted_df = display_df.copy()
        if 'Price' in formatted_df.columns:
            formatted_df['Price'] = formatted_df['Price'].apply(lambda x: f"£{x:.1f}m")
        if 'PPG' in formatted_df.columns:
            formatted_df['PPG'] = formatted_df['PPG'].apply(lambda x: f"{x:.1f}")
        if 'Value' in formatted_df.columns:
            formatted_df['Value'] = formatted_df['Value'].apply(lambda x: f"{x:.1f}")
        if 'Ownership' in formatted_df.columns:
            formatted_df['Ownership'] = formatted_df['Ownership'].apply(lambda x: f"{x:.1f}%")
        if 'Form' in formatted_df.columns:
            formatted_df['Form'] = formatted_df['Form'].apply(lambda x: f"{x:.1f}")
        
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
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"fpl_players_{len(filtered_df)}_results.csv",
            mime="text/csv"
        )
    
    with tab2:
        if len(filtered_df) == 0:
            st.warning("No players match your filters")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top performers
            top_n = st.slider("Show top N players:", 5, min(20, len(filtered_df)), 10)
            top_players = filtered_df.nlargest(top_n, 'total_points')
            
            fig = px.bar(
                top_players,
                x='total_points',
                y='Player',
                orientation='h',
                title=f"Top {top_n} Point Scorers",
                color='total_points',
                color_continuous_scale='viridis'
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Price vs Points
            fig2 = px.scatter(
                filtered_df,
                x='Price',
                y='total_points',
                color='Position',
                size='Ownership',
                hover_data=['Player', 'Team'],
                title="Price vs Total Points"
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        if len(filtered_df) == 0:
            st.warning("No players match your filters")
            return
        
        # Player selection
        player_options = [f"{row['Player']} ({row['Team']}) - £{row['Price']:.1f}m" 
                         for _, row in filtered_df.iterrows()]
        
        selected_player_str = st.selectbox("Select player:", player_options)
        
        if selected_player_str:
            player_name = selected_player_str.split(' (')[0]
            player = filtered_df[filtered_df['Player'] == player_name].iloc[0]
            
            # Player metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Points", int(player['total_points']))
            col2.metric("Price", f"£{player['Price']:.1f}m")
            col3.metric("PPG", f"{player['PPG']:.1f}")
            col4.metric("Ownership", f"{player['Ownership']:.1f}%")
            col5.metric("Value", f"{player['Value']:.1f}")
            
            # Detailed stats
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Performance:**")
                st.write(f"Goals: {int(player['goals_scored'])}")
                st.write(f"Assists: {int(player['assists'])}")
                st.write(f"Clean Sheets: {int(player['clean_sheets'])}")
                st.write(f"Bonus: {int(player['bonus'])}")
            
            with col2:
                st.write("**Advanced:**")
                st.write(f"ICT Index: {player['ict_index']:.1f}")
                st.write(f"Expected Goals: {player['expected_goals']:.2f}")
                st.write(f"Expected Assists: {player['expected_assists']:.2f}")
                st.write(f"Minutes: {int(player['minutes'])}")

def fixtures_page():
    """Fixtures difficulty analysis page"""
    st.header("🗓️ Fixture Difficulty Analysis")
    
    _, fixtures_df, teams_df, _ = load_fpl_data()
    
    if fixtures_df.empty or teams_df.empty:
        st.error("No fixtures data available")
        return
    
    # Sidebar filters
    st.sidebar.header("🎯 Fixture Filters")
    
    # Team selection
    team_options = [(row['name'], row['id']) for _, row in teams_df.iterrows()]
    team_names = [name for name, _ in team_options]
    selected_team_name = st.sidebar.selectbox("Select Team:", team_names)
    selected_team_id = next(team_id for name, team_id in team_options if name == selected_team_name)
    
    # Rolling window
    window = st.sidebar.slider("Rolling Window (Gameweeks):", 1, 10, 5)
    
    # Calculate difficulty
    difficulty_data = calculate_fixture_difficulty(fixtures_df, selected_team_id, window)
    
    if difficulty_data.empty:
        st.warning(f"No fixture data available for {selected_team_name}")
        return
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Fixtures", len(difficulty_data))
    with col2:
        st.metric("Avg Difficulty", f"{difficulty_data['difficulty'].mean():.2f}")
    with col3:
        next_5_avg = difficulty_data.head(5)['difficulty'].mean() if len(difficulty_data) >= 5 else difficulty_data['difficulty'].mean()
        st.metric("Next 5 GWs", f"{next_5_avg:.2f}")
    with col4:
        st.metric(f"Rolling {window}-GW", f"{difficulty_data['rolling_difficulty'].iloc[-1]:.2f}")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📈 Difficulty Trend", "📋 Fixtures Table", "📊 Analysis"])
    
    with tab1:
        st.subheader(f"{selected_team_name} - Fixture Difficulty Trend")
        
        # Create trend chart
        fig = go.Figure()
        
        # Raw difficulty points
        fig.add_trace(go.Scatter(
            x=difficulty_data['event'],
            y=difficulty_data['difficulty'],
            mode='markers',
            name='Fixture Difficulty',
            marker=dict(size=8, opacity=0.7),
            hovertemplate='<b>GW %{x}</b><br>Difficulty: %{y}<br>Opponent: %{customdata}<extra></extra>',
            customdata=difficulty_data['opponent']
        ))
        
        # Rolling average line
        fig.add_trace(go.Scatter(
            x=difficulty_data['event'],
            y=difficulty_data['rolling_difficulty'],
            mode='lines+markers',
            name=f'{window}-GW Rolling Average',
            line=dict(width=3, color='red'),
            hovertemplate='<b>GW %{x}</b><br>Rolling Avg: %{y:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            xaxis_title="Gameweek",
            yaxis_title="Difficulty (1=Easy, 5=Hard)",
            yaxis=dict(range=[0.5, 5.5]),
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Upcoming Fixtures")
        
        # Prepare fixtures table
        upcoming_fixtures = difficulty_data.head(15).copy()
        
        # Format the display
        fixtures_display = upcoming_fixtures[['event', 'opponent', 'venue', 'difficulty']].copy()
        fixtures_display.columns = ['GW', 'Opponent', 'Venue', 'Difficulty']
        
        # Color coding function
        def color_difficulty(val):
            if val == 5:
                return 'background-color: #ffcdd2'  # Light red
            elif val == 4:
                return 'background-color: #fff3e0'  # Light orange
            elif val == 3:
                return 'background-color: #fff9c4'  # Light yellow
            elif val == 2:
                return 'background-color: #c8e6c9'  # Light green
            else:
                return 'background-color: #e8f5e8'  # Very light green
        
        # Apply styling
        styled_df = fixtures_display.style.map(color_difficulty, subset=['Difficulty'])
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Download fixtures
        csv = fixtures_display.to_csv(index=False)
        st.download_button(
            "📥 Download Fixtures CSV",
            csv,
            f"{selected_team_name}_fixtures.csv",
            "text/csv"
        )
    
    with tab3:
        st.subheader("Difficulty Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Difficulty distribution
            difficulty_counts = difficulty_data['difficulty'].value_counts().sort_index()
            fig_dist = px.bar(
                x=difficulty_counts.index,
                y=difficulty_counts.values,
                title="Difficulty Distribution",
                labels={'x': 'Difficulty Level', 'y': 'Number of Fixtures'},
                color=difficulty_counts.values,
                color_continuous_scale='RdYlGn_r'
            )
            fig_dist.update_layout(height=400)
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            # Home vs Away difficulty
            venue_difficulty = difficulty_data.groupby('venue')['difficulty'].mean().reset_index()
            fig_venue = px.bar(
                venue_difficulty,
                x='venue',
                y='difficulty',
                title="Average Difficulty by Venue",
                color='difficulty',
                color_continuous_scale='RdYlGn_r'
            )
            fig_venue.update_layout(height=400)
            st.plotly_chart(fig_venue, use_container_width=True)
        
        # Difficulty periods analysis
        st.subheader("Difficulty Periods")
        
        # Find easy and hard periods
        easy_fixtures = difficulty_data[difficulty_data['difficulty'] <= 2]
        hard_fixtures = difficulty_data[difficulty_data['difficulty'] >= 4]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**🟢 Easy Fixtures (Difficulty ≤ 2):**")
            if not easy_fixtures.empty:
                for _, fixture in easy_fixtures.head(5).iterrows():
                    st.write(f"GW{fixture['event']}: vs {fixture['opponent']} ({fixture['venue']}) - {fixture['difficulty']}")
            else:
                st.write("No easy fixtures in the upcoming period")
        
        with col2:
            st.write("**🔴 Hard Fixtures (Difficulty ≥ 4):**")
            if not hard_fixtures.empty:
                for _, fixture in hard_fixtures.head(5).iterrows():
                    st.write(f"GW{fixture['event']}: vs {fixture['opponent']} ({fixture['venue']}) - {fixture['difficulty']}")
            else:
                st.write("No particularly hard fixtures in the upcoming period")

def main():
    st.title("⚽ FPL Analytics Dashboard")
    st.markdown("### Complete Fantasy Premier League Analysis Tool")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["📊 Player Statistics", "🗓️ Fixture Difficulty"]
    )
    
    if page == "📊 Player Statistics":
        players_page()
    elif page == "🗓️ Fixture Difficulty":
        fixtures_page()

if __name__ == "__main__":
    main()