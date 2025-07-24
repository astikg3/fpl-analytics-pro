#!/usr/bin/env python3
"""
Simple, reliable FPL Player Statistics - No complex formatting
"""
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Page config
st.set_page_config(page_title="FPL Stats", page_icon="⚽", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    """Load FPL data"""
    try:
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
        data = response.json()
        
        players = pd.DataFrame(data['elements'])
        teams = pd.DataFrame(data['teams'])
        positions = pd.DataFrame(data['element_types'])
        
        # Simple mapping
        team_map = dict(zip(teams['id'], teams['name']))
        pos_map = dict(zip(positions['id'], positions['singular_name']))
        
        players['team_name'] = players['team'].map(team_map)
        players['position'] = players['element_type'].map(pos_map)
        players['price'] = players['now_cost'] / 10
        
        return players
    except:
        return pd.DataFrame()

def main():
    st.title("⚽ FPL Player Statistics")
    
    # Load data
    df = load_data()
    if df.empty:
        st.error("Failed to load data")
        return
    
    st.success(f"Loaded {len(df)} players")
    
    # Simple filters in sidebar
    st.sidebar.header("Filters")
    
    position = st.sidebar.selectbox("Position", ['All'] + list(df['position'].unique()))
    team = st.sidebar.selectbox("Team", ['All'] + list(df['team_name'].unique()))
    min_points = st.sidebar.number_input("Min Points", 0, int(df['total_points'].max()), 0)
    
    # Apply filters
    filtered = df.copy()
    if position != 'All':
        filtered = filtered[filtered['position'] == position]
    if team != 'All':
        filtered = filtered[filtered['team_name'] == team]
    filtered = filtered[filtered['total_points'] >= min_points]
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Players", len(filtered))
    col2.metric("Avg Price", f"£{filtered['price'].mean():.1f}m")
    col3.metric("Avg Points", f"{filtered['total_points'].mean():.0f}")
    col4.metric("Top Score", filtered['total_points'].max())
    
    # Column selection
    all_cols = ['web_name', 'team_name', 'position', 'price', 'total_points', 'points_per_game',
                'goals_scored', 'assists', 'clean_sheets', 'bonus', 'selected_by_percent',
                'ict_index', 'form', 'expected_goals', 'expected_assists', 'minutes']
    
    selected_cols = st.multiselect(
        "Select columns:",
        all_cols,
        default=['web_name', 'team_name', 'position', 'price', 'total_points', 'points_per_game']
    )
    
    if selected_cols:
        # Sort options
        sort_col = st.selectbox("Sort by:", selected_cols)
        ascending = st.checkbox("Ascending", False)
        
        # Display table
        display_df = filtered[selected_cols].sort_values(sort_col, ascending=ascending)
        
        st.dataframe(display_df, use_container_width=True, height=600)
        
        # Download
        csv = display_df.to_csv(index=False)
        st.download_button("Download CSV", csv, "fpl_data.csv", "text/csv")
        
        # Simple visualizations
        if len(filtered) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                top_10 = filtered.nlargest(10, 'total_points')
                fig1 = px.bar(top_10, x='total_points', y='web_name', 
                             orientation='h', title="Top 10 Scorers")
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = px.scatter(filtered, x='price', y='total_points', 
                                color='position', title="Price vs Points")
                st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()