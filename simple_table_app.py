#!/usr/bin/env python3
"""
Simple FPL Player Statistics Table - Focused on data display with filtering
"""
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Page config
st.set_page_config(
    page_title="FPL Player Stats",
    page_icon="⚽",
    layout="wide"
)

@st.cache_data(ttl=300)
def get_fpl_data():
    """Load FPL data with error handling"""
    try:
        st.info("Loading FPL data...")
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=15)
        data = response.json()
        
        # Process data
        players = pd.DataFrame(data['elements'])
        teams = pd.DataFrame(data['teams'])
        positions = pd.DataFrame(data['element_types'])
        
        # Create lookup dictionaries
        team_lookup = dict(zip(teams['id'], teams['name']))
        position_lookup = dict(zip(positions['id'], positions['singular_name']))
        
        # Add human-readable columns
        players['Team'] = players['team'].map(team_lookup)
        players['Position'] = players['element_type'].map(position_lookup)
        players['Price'] = players['now_cost'] / 10
        players['Player'] = players['web_name']
        
        # Calculate useful metrics
        players['Value'] = players['total_points'] / players['Price']
        players['PPG'] = players['points_per_game']
        players['Ownership'] = players['selected_by_percent']
        players['Form'] = players['form']
        
        st.success(f"✅ Loaded {len(players)} players successfully!")
        return players
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()

def main():
    st.title("⚽ FPL Player Statistics")
    st.markdown("---")
    
    # Load data
    df = get_fpl_data()
    
    if df.empty:
        st.stop()
    
    # Sidebar filters
    st.sidebar.header("🎯 Filters")
    
    # Position filter
    positions = st.sidebar.multiselect(
        "Position", 
        options=df['Position'].unique(),
        default=df['Position'].unique()
    )
    
    # Team filter
    teams = st.sidebar.multiselect(
        "Team",
        options=sorted(df['Team'].unique()),
        default=[]
    )
    
    # Price range
    price_range = st.sidebar.slider(
        "Price Range (£m)",
        min_value=float(df['Price'].min()),
        max_value=float(df['Price'].max()),
        value=(4.0, 15.0),
        step=0.1
    )
    
    # Points filter
    min_points = st.sidebar.number_input(
        "Minimum Total Points", 
        min_value=0, 
        max_value=int(df['total_points'].max()),
        value=0,
        step=10
    )
    
    # Apply filters
    filtered_df = df[
        (df['Position'].isin(positions)) &
        (df['Price'] >= price_range[0]) &
        (df['Price'] <= price_range[1]) &
        (df['total_points'] >= min_points)
    ]
    
    if teams:
        filtered_df = filtered_df[filtered_df['Team'].isin(teams)]
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Players", len(filtered_df))
    with col2:
        st.metric("Avg Price", f"£{filtered_df['Price'].mean():.1f}m")
    with col3:
        st.metric("Avg Points", f"{filtered_df['total_points'].mean():.0f}")
    with col4:
        st.metric("Top Score", f"{filtered_df['total_points'].max()}")
    
    st.markdown("---")
    
    # Main table configuration
    st.subheader("📊 Player Statistics Table")
    
    # Column selection
    available_columns = {
        'Player': 'Player',
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
        'red_cards': 'Red Cards',
        'saves': 'Saves',
        'goals_conceded': 'Goals Conceded'
    }
    
    # Default columns for display
    default_cols = ['Player', 'Team', 'Position', 'Price', 'total_points', 'PPG', 'Ownership']
    
    selected_cols = st.multiselect(
        "Select columns to display:",
        options=list(available_columns.keys()),
        default=default_cols,
        help="Choose which statistics to show in the table"
    )
    
    if not selected_cols:
        st.warning("Please select at least one column to display")
        st.stop()
    
    # Sort options
    col1, col2 = st.columns(2)
    with col1:
        sort_column = st.selectbox(
            "Sort by:",
            options=selected_cols,
            index=selected_cols.index('total_points') if 'total_points' in selected_cols else 0
        )
    with col2:
        sort_order = st.selectbox("Order:", ["Descending", "Ascending"])
    
    # Apply sorting
    ascending = sort_order == "Ascending"
    display_df = filtered_df[selected_cols].sort_values(sort_column, ascending=ascending)
    
    # Format the dataframe for display
    formatted_df = display_df.copy()
    if 'Price' in formatted_df.columns:
        formatted_df['Price'] = formatted_df['Price'].apply(lambda x: f"£{x:.1f}m")
    if 'PPG' in formatted_df.columns:
        formatted_df['PPG'] = formatted_df['PPG'].apply(lambda x: f"{x:.1f}")
    if 'Value' in formatted_df.columns:
        formatted_df['Value'] = formatted_df['Value'].apply(lambda x: f"{x:.1f}")
    if 'Ownership' in formatted_df.columns:
        formatted_df['Ownership'] = formatted_df['Ownership'].apply(lambda x: f"{x:.1f}%")
    
    # Display table
    st.dataframe(
        formatted_df,
        use_container_width=True,
        height=600
    )
    
    # Download option
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="fpl_player_stats.csv",
        mime="text/csv"
    )
    
    # Quick visualizations
    if len(filtered_df) > 0:
        st.markdown("---")
        st.subheader("📈 Quick Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top performers
            top_n = min(10, len(filtered_df))
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
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Price vs Points scatter
            fig2 = px.scatter(
                filtered_df,
                x='Price',
                y='total_points',
                color='Position',
                hover_data=['Player', 'Team'],
                title="Price vs Total Points"
            )
            st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()