#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import numpy as np

# Page config
st.set_page_config(
    page_title="FPL Analytics Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stSelectbox > div > div {
        background-color: white;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_fpl_data():
    """Load and process FPL data with caching"""
    try:
        with st.spinner("Loading FPL data..."):
            # Bootstrap data
            bootstrap_response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
            bootstrap_data = bootstrap_response.json()
            
            # Create DataFrames
            players_df = pd.DataFrame(bootstrap_data['elements'])
            teams_df = pd.DataFrame(bootstrap_data['teams'])
            positions_df = pd.DataFrame(bootstrap_data['element_types'])
            
            # Create mapping dictionaries
            team_map = dict(zip(teams_df['id'], teams_df['name']))
            position_map = dict(zip(positions_df['id'], positions_df['singular_name']))
            
            # Add mapped columns
            players_df['team_name'] = players_df['team'].map(team_map)
            players_df['position'] = players_df['element_type'].map(position_map)
            players_df['price'] = players_df['now_cost'] / 10
            
            # Calculate additional metrics
            players_df['value_score'] = players_df['total_points'] / players_df['price']
            players_df['goals_per_game'] = players_df['goals_scored'] / players_df['starts'].replace(0, 1)
            players_df['assists_per_game'] = players_df['assists'] / players_df['starts'].replace(0, 1)
            
            # Filter out unavailable players
            players_df = players_df[players_df['status'] != 'u']
            
            return players_df, teams_df, positions_df
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def main():
    # Header
    st.markdown('<h1 class="main-header">⚽ FPL Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    players_df, teams_df, positions_df = load_fpl_data()
    
    if players_df.empty:
        st.error("Failed to load data. Please refresh the page.")
        return
    
    # Sidebar filters
    st.sidebar.header("🎯 Filters")
    
    # Position filter
    positions = ['All'] + sorted(players_df['position'].unique().tolist())
    selected_position = st.sidebar.selectbox("Position", positions)
    
    # Team filter
    teams = ['All'] + sorted(players_df['team_name'].unique().tolist())
    selected_team = st.sidebar.selectbox("Team", teams)
    
    # Price range
    min_price, max_price = st.sidebar.slider(
        "Price Range (£m)",
        min_value=float(players_df['price'].min()),
        max_value=float(players_df['price'].max()),
        value=(4.0, 15.0),
        step=0.1
    )
    
    # Points range
    min_points = st.sidebar.number_input("Minimum Points", value=0, step=10)
    
    # Ownership filter
    min_ownership = st.sidebar.slider("Minimum Ownership %", 0.0, 100.0, 0.0, 0.1)
    
    # Apply filters
    filtered_df = players_df.copy()
    
    if selected_position != 'All':
        filtered_df = filtered_df[filtered_df['position'] == selected_position]
    
    if selected_team != 'All':
        filtered_df = filtered_df[filtered_df['team_name'] == selected_team]
    
    filtered_df = filtered_df[
        (filtered_df['price'] >= min_price) & 
        (filtered_df['price'] <= max_price) &
        (filtered_df['total_points'] >= min_points) &
        (filtered_df['selected_by_percent'] >= min_ownership)
    ]
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Players", len(filtered_df))
    with col2:
        st.metric("Avg Price", f"£{filtered_df['price'].mean():.1f}m")
    with col3:
        st.metric("Avg Points", f"{filtered_df['total_points'].mean():.0f}")
    with col4:
        st.metric("Top Scorer", f"{filtered_df['total_points'].max()}")
    with col5:
        st.metric("Best Value", f"{filtered_df['value_score'].max():.1f}")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Table", "📈 Visualizations", "🔍 Player Analysis", "🏆 Comparisons"])
    
    with tab1:
        st.header("📊 Player Statistics Table")
        
        # Column selection
        all_columns = [
            'web_name', 'team_name', 'position', 'price', 'total_points', 'points_per_game',
            'goals_scored', 'assists', 'clean_sheets', 'bonus', 'ict_index', 'form',
            'expected_goals', 'expected_assists', 'minutes', 'starts', 'selected_by_percent',
            'value_score', 'creativity', 'influence', 'threat', 'yellow_cards', 'red_cards'
        ]
        
        selected_columns = st.multiselect(
            "Select columns to display:",
            all_columns,
            default=['web_name', 'team_name', 'position', 'price', 'total_points', 'points_per_game', 'selected_by_percent']
        )
        
        if selected_columns:
            # Sort options
            sort_by = st.selectbox("Sort by:", selected_columns, index=selected_columns.index('total_points') if 'total_points' in selected_columns else 0)
            ascending = st.checkbox("Ascending order", value=False)
            
            # Display table
            display_df = filtered_df[selected_columns].sort_values(sort_by, ascending=ascending)
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=600,
                column_config={
                    'web_name': st.column_config.TextColumn('Player'),
                    'team_name': st.column_config.TextColumn('Team'),
                    'position': st.column_config.TextColumn('Position'),
                    'price': st.column_config.NumberColumn('Price (£m)', format="%.1f"),
                    'total_points': st.column_config.NumberColumn('Points'),
                    'points_per_game': st.column_config.NumberColumn('PPG', format="%.1f"),
                    'selected_by_percent': st.column_config.NumberColumn('Ownership %', format="%.1f"),
                    'value_score': st.column_config.NumberColumn('Value Score', format="%.1f"),
                    'expected_goals': st.column_config.NumberColumn('xG', format="%.2f"),
                    'expected_assists': st.column_config.NumberColumn('xA', format="%.2f"),
                    'ict_index': st.column_config.NumberColumn('ICT Index', format="%.1f")
                }
            )
            
            # Download button
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"fpl_players_{selected_position.lower()}.csv",
                mime="text/csv"
            )
    
    with tab2:
        st.header("📈 Data Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Points vs Price scatter
            fig_scatter = px.scatter(
                filtered_df,
                x='price',
                y='total_points',
                color='position',
                size='selected_by_percent',
                hover_data=['web_name', 'team_name'],
                title="Points vs Price (Size = Ownership %)"
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with col2:
            # Top performers bar chart
            top_n = st.slider("Top N players", 5, 20, 10)
            top_players = filtered_df.nlargest(top_n, 'total_points')
            
            fig_bar = px.bar(
                top_players,
                x='total_points',
                y='web_name',
                orientation='h',
                color='total_points',
                title=f"Top {top_n} Point Scorers"
            )
            fig_bar.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Additional charts
        col3, col4 = st.columns(2)
        
        with col3:
            # Value score analysis
            fig_value = px.scatter(
                filtered_df,
                x='price',
                y='value_score',
                color='position',
                hover_data=['web_name', 'team_name'],
                title="Value Score vs Price"
            )
            fig_value.update_layout(height=400)
            st.plotly_chart(fig_value, use_container_width=True)
        
        with col4:
            # Expected vs Actual goals
            if selected_position in ['Forward', 'Midfielder']:
                fig_expected = px.scatter(
                    filtered_df,
                    x='expected_goals',
                    y='goals_scored',
                    hover_data=['web_name', 'team_name'],
                    title="Expected Goals vs Actual Goals"
                )
                # Add diagonal line
                max_val = max(filtered_df['expected_goals'].max(), filtered_df['goals_scored'].max())
                fig_expected.add_shape(
                    type="line", line=dict(dash="dash"),
                    x0=0, x1=max_val, y0=0, y1=max_val
                )
                fig_expected.update_layout(height=400)
                st.plotly_chart(fig_expected, use_container_width=True)
            else:
                # Clean sheets for defenders/goalkeepers
                fig_cs = px.bar(
                    filtered_df.nlargest(10, 'clean_sheets'),
                    x='clean_sheets',
                    y='web_name',
                    orientation='h',
                    title="Top 10 Clean Sheets"
                )
                fig_cs.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_cs, use_container_width=True)
    
    with tab3:
        st.header("🔍 Individual Player Analysis")
        
        # Player selection
        player_options = filtered_df.apply(
            lambda x: f"{x['web_name']} ({x['team_name']}) - £{x['price']:.1f}m", axis=1
        ).tolist()
        
        if player_options:
            selected_player_str = st.selectbox("Select a player:", player_options)
            
            # Extract player data
            player_name = selected_player_str.split(' (')[0]
            selected_player = filtered_df[filtered_df['web_name'] == player_name].iloc[0]
            
            # Player overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Points", selected_player['total_points'])
            with col2:
                st.metric("Price", f"£{selected_player['price']:.1f}m")
            with col3:
                st.metric("Points per Game", f"{selected_player['points_per_game']:.1f}")
            with col4:
                st.metric("Ownership", f"{selected_player['selected_by_percent']:.1f}%")
            
            # Detailed stats
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Performance Stats")
                stats_data = {
                    'Goals': selected_player['goals_scored'],
                    'Assists': selected_player['assists'],
                    'Clean Sheets': selected_player['clean_sheets'],
                    'Bonus Points': selected_player['bonus'],
                    'Yellow Cards': selected_player['yellow_cards'],
                    'Red Cards': selected_player['red_cards']
                }
                
                for stat, value in stats_data.items():
                    st.write(f"**{stat}:** {value}")
            
            with col2:
                st.subheader("🎯 Advanced Metrics")
                advanced_stats = {
                    'ICT Index': f"{selected_player['ict_index']:.1f}",
                    'Expected Goals': f"{selected_player['expected_goals']:.2f}",
                    'Expected Assists': f"{selected_player['expected_assists']:.2f}",
                    'Form': f"{selected_player['form']:.1f}",
                    'Value Score': f"{selected_player['value_score']:.1f}",
                    'Minutes': selected_player['minutes']
                }
                
                for stat, value in advanced_stats.items():
                    st.write(f"**{stat}:** {value}")
    
    with tab4:
        st.header("🏆 Player Comparisons")
        
        # Multi-select for player comparison
        comparison_players = st.multiselect(
            "Select players to compare:",
            filtered_df.apply(lambda x: f"{x['web_name']} ({x['team_name']})", axis=1).tolist(),
            max_selections=5
        )
        
        if len(comparison_players) >= 2:
            # Extract player names and get their data
            player_names = [p.split(' (')[0] for p in comparison_players]
            comparison_df = filtered_df[filtered_df['web_name'].isin(player_names)]
            
            # Comparison metrics
            comparison_metrics = ['total_points', 'goals_scored', 'assists', 'ict_index', 'value_score', 'price']
            
            fig_comparison = px.bar(
                comparison_df.melt(id_vars=['web_name'], value_vars=comparison_metrics),
                x='variable',
                y='value',
                color='web_name',
                barmode='group',
                title="Player Comparison",
                labels={'variable': 'Metric', 'value': 'Value'}
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Comparison table
            st.subheader("Detailed Comparison")
            comparison_cols = ['web_name', 'team_name', 'position', 'price', 'total_points', 
                             'goals_scored', 'assists', 'ict_index', 'selected_by_percent']
            st.dataframe(comparison_df[comparison_cols], use_container_width=True)
        else:
            st.info("Select at least 2 players to compare")

if __name__ == "__main__":
    main()