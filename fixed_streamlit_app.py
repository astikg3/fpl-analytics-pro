#!/usr/bin/env python3
"""
Fixed FPL Player Statistics Table - Streamlit Version
"""
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import numpy as np

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
        
        st.success(f"✅ Loaded {len(players)} players successfully!")
        return players
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()

def format_dataframe(df, selected_cols):
    """Format dataframe for display with proper handling of data types"""
    if df.empty:
        return df
    
    formatted_df = df[selected_cols].copy()
    
    # Format columns safely
    for col in formatted_df.columns:
        if col == 'Price':
            formatted_df[col] = formatted_df[col].apply(lambda x: f"£{float(x):.1f}m" if pd.notnull(x) else "N/A")
        elif col == 'PPG':
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{float(x):.1f}" if pd.notnull(x) and x != '' else "0.0")
        elif col == 'Value':
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{float(x):.1f}" if pd.notnull(x) and x != '' else "0.0")
        elif col == 'Ownership':
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{float(x):.1f}%" if pd.notnull(x) and x != '' else "0.0%")
        elif col == 'Form':
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{float(x):.1f}" if pd.notnull(x) and x != '' else "0.0")
    
    return formatted_df

def main():
    st.title("⚽ FPL Player Statistics Dashboard")
    st.markdown("### 📊 Comprehensive Player Analysis with Advanced Filtering")
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
    price_min, price_max = st.sidebar.slider(
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
    
    # Ownership filter
    min_ownership = st.sidebar.slider(
        "Minimum Ownership %",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.5
    )
    
    # Apply filters
    filtered_df = df[
        (df['Position'].isin(positions)) &
        (df['Price'] >= price_min) &
        (df['Price'] <= price_max) &
        (df['total_points'] >= min_points) &
        (df['Ownership'] >= min_ownership)
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
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Data Table", "📈 Visualizations", "🔍 Player Details"])
    
    with tab1:
        st.subheader("📊 Player Statistics Table")
        
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
            page_size = st.selectbox("Rows per page:", [10, 20, 50, 100], index=1)
        
        # Apply sorting
        ascending = sort_order == "Ascending"
        display_df = filtered_df[selected_cols].sort_values(sort_column, ascending=ascending)
        
        # Format the dataframe for display
        formatted_df = format_dataframe(display_df, selected_cols)
        
        # Display table with pagination
        total_rows = len(formatted_df)
        total_pages = (total_rows - 1) // page_size + 1
        
        if total_pages > 1:
            page = st.selectbox(f"Page (of {total_pages}):", range(1, total_pages + 1))
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            display_formatted = formatted_df.iloc[start_idx:end_idx]
        else:
            display_formatted = formatted_df
        
        st.dataframe(
            display_formatted,
            use_container_width=True,
            height=600
        )
        
        # Download option
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"fpl_player_stats_{len(filtered_df)}_players.csv",
            mime="text/csv"
        )
    
    with tab2:
        st.subheader("📈 Data Visualizations")
        
        if len(filtered_df) == 0:
            st.warning("No players match your filters. Try adjusting the filter criteria.")
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
            # Price vs Points scatter
            fig2 = px.scatter(
                filtered_df,
                x='Price',
                y='total_points',
                color='Position',
                size='Ownership',
                hover_data=['Player', 'Team'],
                title="Price vs Total Points (Size = Ownership %)"
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Additional charts
        col3, col4 = st.columns(2)
        
        with col3:
            # Value analysis
            fig3 = px.scatter(
                filtered_df,
                x='Price',
                y='Value',
                color='Position',
                hover_data=['Player', 'Team'],
                title="Value Score vs Price"
            )
            fig3.update_layout(height=400)
            st.plotly_chart(fig3, use_container_width=True)
        
        with col4:
            # Position distribution
            pos_counts = filtered_df['Position'].value_counts()
            fig4 = px.pie(
                values=pos_counts.values,
                names=pos_counts.index,
                title="Player Distribution by Position"
            )
            fig4.update_layout(height=400)
            st.plotly_chart(fig4, use_container_width=True)
    
    with tab3:
        st.subheader("🔍 Individual Player Analysis")
        
        if len(filtered_df) == 0:
            st.warning("No players match your filters.")
            return
        
        # Player selection
        player_options = [f"{row['Player']} ({row['Team']}) - £{row['Price']:.1f}m" 
                         for _, row in filtered_df.iterrows()]
        
        selected_player_str = st.selectbox("Select a player for detailed analysis:", player_options)
        
        if selected_player_str:
            # Extract player data
            player_name = selected_player_str.split(' (')[0]
            selected_player = filtered_df[filtered_df['Player'] == player_name].iloc[0]
            
            # Player overview cards
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Points", int(selected_player['total_points']))
            with col2:
                st.metric("Price", f"£{selected_player['Price']:.1f}m")
            with col3:
                st.metric("Points per Game", f"{selected_player['PPG']:.1f}")
            with col4:
                st.metric("Ownership", f"{selected_player['Ownership']:.1f}%")
            with col5:
                st.metric("Value Score", f"{selected_player['Value']:.1f}")
            
            # Detailed stats in columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Performance Stats")
                performance_data = {
                    'Goals': int(selected_player['goals_scored']),
                    'Assists': int(selected_player['assists']),
                    'Clean Sheets': int(selected_player['clean_sheets']),
                    'Bonus Points': int(selected_player['bonus']),
                    'Minutes Played': int(selected_player['minutes']),
                    'Starts': int(selected_player['starts'])
                }
                
                for stat, value in performance_data.items():
                    st.write(f"**{stat}:** {value}")
            
            with col2:
                st.subheader("🎯 Advanced Metrics")
                advanced_data = {
                    'ICT Index': f"{selected_player['ict_index']:.1f}",
                    'Expected Goals': f"{selected_player['expected_goals']:.2f}",
                    'Expected Assists': f"{selected_player['expected_assists']:.2f}",
                    'Form': f"{selected_player['Form']:.1f}",
                    'Yellow Cards': int(selected_player['yellow_cards']),
                    'Red Cards': int(selected_player['red_cards'])
                }
                
                for stat, value in advanced_data.items():
                    st.write(f"**{stat}:** {value}")

if __name__ == "__main__":
    main()