#!/usr/bin/env python3
"""
Simple HTML table version - fastest loading with basic filtering
"""
from flask import Flask, render_template_string, request
import pandas as pd
import requests

app = Flask(__name__)

def get_fpl_data():
    """Load FPL data"""
    try:
        response = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/", timeout=10)
        data = response.json()
        
        players = pd.DataFrame(data['elements'])
        teams = pd.DataFrame(data['teams'])
        positions = pd.DataFrame(data['element_types'])
        
        team_lookup = dict(zip(teams['id'], teams['name']))
        position_lookup = dict(zip(positions['id'], positions['singular_name']))
        
        players['team_name'] = players['team'].map(team_lookup)
        players['position'] = players['element_type'].map(position_lookup)
        players['price'] = players['now_cost'] / 10
        players['value'] = players['total_points'] / players['price']
        
        return players
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

# Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>⚽ FPL Player Statistics</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #1f77b4; color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
        .filters { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stats { display: flex; gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 15px; border-radius: 8px; text-align: center; flex: 1; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stat-number { font-size: 24px; font-weight: bold; color: #1f77b4; }
        .stat-label { color: #666; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #1f77b4; color: white; font-weight: bold; }
        tr:hover { background: #f8f9fa; }
        .filter-row { display: flex; gap: 20px; margin-bottom: 15px; align-items: center; }
        select, input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .position-gk { background: #ffeb3b; }
        .position-def { background: #4caf50; color: white; }
        .position-mid { background: #2196f3; color: white; }
        .position-fwd { background: #f44336; color: white; }
        .btn { background: #1f77b4; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #1565c0; }
    </style>
    <script>
        function filterTable() {
            const position = document.getElementById('position').value;
            const team = document.getElementById('team').value;
            const minPoints = parseInt(document.getElementById('minPoints').value) || 0;
            const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
            const maxPrice = parseFloat(document.getElementById('maxPrice').value) || 20;
            
            const rows = document.querySelectorAll('#playerTable tbody tr');
            let visibleCount = 0;
            
            rows.forEach(row => {
                const rowPosition = row.cells[2].textContent;
                const rowTeam = row.cells[1].textContent;
                const rowPoints = parseInt(row.cells[4].textContent);
                const rowPrice = parseFloat(row.cells[3].textContent.replace('£', '').replace('m', ''));
                
                const positionMatch = position === 'all' || rowPosition === position;
                const teamMatch = team === 'all' || rowTeam === team;
                const pointsMatch = rowPoints >= minPoints;
                const priceMatch = rowPrice >= minPrice && rowPrice <= maxPrice;
                
                if (positionMatch && teamMatch && pointsMatch && priceMatch) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            document.getElementById('playerCount').textContent = visibleCount;
        }
        
        function sortTable(column) {
            const table = document.getElementById('playerTable');
            const tbody = table.getElementsByTagName('tbody')[0];
            const rows = Array.from(tbody.rows);
            
            rows.sort((a, b) => {
                let aVal = a.cells[column].textContent;
                let bVal = b.cells[column].textContent;
                
                // Handle numeric columns
                if (column === 3) { // Price
                    aVal = parseFloat(aVal.replace('£', '').replace('m', ''));
                    bVal = parseFloat(bVal.replace('£', '').replace('m', ''));
                } else if (column >= 4) { // Numeric columns
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                }
                
                return bVal - aVal; // Descending order
            });
            
            rows.forEach(row => tbody.appendChild(row));
        }
    </script>
</head>
<body>
    <div class="header">
        <h1>⚽ FPL Player Statistics Dashboard</h1>
        <p>Fast, lightweight player analysis tool</p>
    </div>
    
    <div class="filters">
        <h3>🎯 Filters</h3>
        <div class="filter-row">
            <label>Position:</label>
            <select id="position" onchange="filterTable()">
                <option value="all">All Positions</option>
                {% for pos in positions %}
                <option value="{{ pos }}">{{ pos }}</option>
                {% endfor %}
            </select>
            
            <label>Team:</label>
            <select id="team" onchange="filterTable()">
                <option value="all">All Teams</option>
                {% for team in teams %}
                <option value="{{ team }}">{{ team }}</option>
                {% endfor %}
            </select>
            
            <label>Min Points:</label>
            <input type="number" id="minPoints" placeholder="0" onchange="filterTable()" style="width: 80px;">
            
            <label>Price Range:</label>
            <input type="number" id="minPrice" placeholder="4.0" step="0.1" onchange="filterTable()" style="width: 80px;">
            <span>to</span>
            <input type="number" id="maxPrice" placeholder="15.0" step="0.1" onchange="filterTable()" style="width: 80px;">
            
            <button class="btn" onclick="location.reload()">Reset</button>
        </div>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number" id="playerCount">{{ total_players }}</div>
            <div class="stat-label">Players</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ avg_price }}</div>
            <div class="stat-label">Avg Price</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ avg_points }}</div>
            <div class="stat-label">Avg Points</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ top_score }}</div>
            <div class="stat-label">Top Score</div>
        </div>
    </div>
    
    <table id="playerTable">
        <thead>
            <tr>
                <th onclick="sortTable(0)">Player ↕</th>
                <th onclick="sortTable(1)">Team ↕</th>
                <th onclick="sortTable(2)">Position ↕</th>
                <th onclick="sortTable(3)">Price ↕</th>
                <th onclick="sortTable(4)">Points ↕</th>
                <th onclick="sortTable(5)">PPG ↕</th>
                <th onclick="sortTable(6)">Goals ↕</th>
                <th onclick="sortTable(7)">Assists ↕</th>
                <th onclick="sortTable(8)">Ownership ↕</th>
                <th onclick="sortTable(9)">Value ↕</th>
                <th onclick="sortTable(10)">Form ↕</th>
            </tr>
        </thead>
        <tbody>
            {% for _, player in players.iterrows() %}
            <tr class="position-{{ player.position.lower()[:3] }}">
                <td><strong>{{ player.web_name }}</strong></td>
                <td>{{ player.team_name }}</td>
                <td>{{ player.position }}</td>
                <td>£{{ "%.1f"|format(player.price) }}m</td>
                <td>{{ player.total_points }}</td>
                <td>{{ "%.1f"|format(player.points_per_game) }}</td>
                <td>{{ player.goals_scored }}</td>
                <td>{{ player.assists }}</td>
                <td>{{ "%.1f"|format(player.selected_by_percent) }}%</td>
                <td>{{ "%.1f"|format(player.value) }}</td>
                <td>{{ "%.1f"|format(player.form) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div style="margin-top: 20px; text-align: center; color: #666;">
        <p>Data refreshed from FPL API • Click column headers to sort • Use filters above to narrow results</p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_fpl_data()
    
    if df.empty:
        return "<h1>Error loading FPL data. Please try again.</h1>"
    
    # Calculate summary stats
    stats = {
        'total_players': len(df),
        'avg_price': f"£{df['price'].mean():.1f}m",
        'avg_points': f"{df['total_points'].mean():.0f}",
        'top_score': df['total_points'].max(),
        'positions': sorted(df['position'].unique()),
        'teams': sorted(df['team_name'].unique()),
        'players': df.sort_values('total_points', ascending=False)
    }
    
    return render_template_string(HTML_TEMPLATE, **stats)

if __name__ == '__main__':
    print("🚀 Starting Simple HTML FPL Dashboard...")
    print("📊 Open: http://localhost:8057")
    app.run(debug=True, host='0.0.0.0', port=8057)