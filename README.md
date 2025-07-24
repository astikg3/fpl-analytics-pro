# ⚽ FPL Analytics Pro

A comprehensive Fantasy Premier League analytics dashboard built with Python and Streamlit, providing advanced player statistics, granular fixture difficulty analysis, and team performance metrics.

![FPL Analytics Dashboard](https://img.shields.io/badge/FPL-Analytics-blue) ![Python](https://img.shields.io/badge/Python-3.9+-green) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red)

## 🚀 Features

### 📊 Player Statistics
- **Advanced Filtering**: Filter by position, team, price range, points, and ownership
- **Comprehensive Data**: 20+ statistical categories including xG, xA, ICT index, form
- **Smart Sorting**: Proper numeric sorting with pagination
- **Export Options**: Download filtered results as CSV
- **Visualizations**: Interactive charts for performance analysis

### 🗓️ Fixture Analysis  
- **Granular Difficulty**: 0-10 scale difficulty ratings (vs basic 1-5 FPL ratings)
- **Multi-Team Comparison**: Compare fixtures for multiple teams simultaneously
- **Rolling Averages**: Customizable difficulty trend analysis
- **Venue Analysis**: Home/away specific difficulty calculations
- **Visual Trends**: Interactive charts showing difficulty over time

### 🏟️ Team Statistics
- **Performance Metrics**: Goals, assists, points aggregated by team
- **Strength Ratings**: Official FPL team strength analysis (attack/defense)
- **Value Analysis**: Team performance vs total player investment
- **Player Insights**: Top scorers and most expensive players per team

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/fpl-analytics-pro.git
cd fpl-analytics-pro

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run enhanced_dashboard.py
```

### Dependencies
```
streamlit==1.47.0
plotly==5.17.0
pandas==2.1.4
requests==2.31.0
numpy==1.26.4
```

## 📱 Usage

1. **Start the Application**:
   ```bash
   streamlit run enhanced_dashboard.py
   ```

2. **Navigate the Dashboard**:
   - **Player Statistics**: Analyze individual player performance and value
   - **Fixture Analysis**: Plan transfers based on upcoming fixture difficulty
   - **Team Statistics**: Compare team performance and strength

3. **Key Features**:
   - Use sidebar filters to narrow down analysis
   - Click column headers to sort data
   - Download any analysis as CSV
   - Hover over charts for detailed information

## 📊 Data Source

This application uses the official Fantasy Premier League API:
- **Endpoint**: `https://fantasy.premierleague.com/api/`
- **Data**: Real-time player stats, fixtures, and team information
- **Update Frequency**: Data refreshes every 5 minutes via caching
- **Coverage**: Current Premier League season with 659 players across 20 teams

## 🎯 Key Metrics Explained

### Player Metrics
- **Value Score**: Total points divided by player price (points per £million)
- **PPG**: Points per game played
- **xG/xA**: Expected goals and assists based on shot quality
- **ICT Index**: Influence, Creativity, and Threat combined metric

### Fixture Difficulty
- **Granular Scale**: 0-10 difficulty rating (vs FPL's basic 1-5)
- **Calculation**: Based on opponent's attack/defense strength ratings
- **Venue Adjusted**: Different ratings for home vs away fixtures
- **Rolling Average**: Smoothed difficulty trends over multiple gameweeks

### Team Strength
- **Official Ratings**: FPL's internal team strength metrics (1000-1400 scale)
- **Attack/Defense**: Separate ratings for attacking and defensive strength
- **Home/Away**: Different strength ratings based on venue

## 🔧 Technical Architecture

### Data Processing
- **Caching**: Streamlit caching for optimal performance (5-minute TTL)
- **Processing**: Pandas for data manipulation and aggregation
- **Calculations**: Custom algorithms for difficulty and value metrics

### Visualization
- **Charts**: Plotly for interactive visualizations
- **Tables**: Streamlit's native data display with sorting and filtering
- **Styling**: Custom CSS for enhanced user interface

### Performance
- **Load Time**: ~3-5 seconds initial load
- **Data Volume**: 659 players × 97 fields efficiently processed
- **Memory Usage**: Optimized with pandas operations

## 📈 Analytics Capabilities

### Player Analysis
- Performance trends and form analysis
- Price vs points value identification
- Position-specific comparisons
- Ownership trend analysis

### Fixture Planning
- Upcoming difficulty assessment
- Best/worst fixture runs identification
- Multi-gameweek planning
- Venue advantage analysis

### Team Comparison
- Squad strength evaluation
- Investment efficiency analysis
- Attack vs defense balance
- Player distribution insights

## 🚦 Project Status

**Current Version**: 1.0.0
- ✅ Core functionality complete
- ✅ All major features implemented
- ✅ Data accuracy validated
- ✅ Performance optimized

## 🤝 Contributing

This project was developed as a comprehensive FPL analytics solution. Feel free to fork and enhance!

### Potential Enhancements
- Historical season data integration
- Predictive modeling for player performance
- Price change tracking and alerts
- Mobile-responsive design
- User authentication and saved preferences

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **FPL API**: Official Fantasy Premier League data source
- **Streamlit**: Excellent framework for rapid dashboard development
- **Plotly**: Interactive visualization capabilities
- **Pandas**: Powerful data manipulation tools

## 📞 Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

**Built for FPL managers who want data-driven insights for better decision making.** 🏆