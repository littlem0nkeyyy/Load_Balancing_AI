from flask import Flask, jsonify, render_template_string
import threading
import time
from ai_proactive_agent import AIProactiveAgent

app = Flask(__name__)

# Global state
ai_agent = None
dashboard_data = {
    "conf_threshold": 0.7,
    "idle_threshold": 5.0,
    "last_action": "STAY",
    "last_decision_time": None,
    "servers": [],
    "last_learning_time": None,
    "total_decisions": 0,
    "total_opens": 0,
    "total_closes": 0
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Load Balancer Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }

        .header .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card h3 {
            color: #00d4ff;
            font-size: 0.85em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #fff;
        }

        .thresholds-section {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        .thresholds-section h2 {
            color: #00d4ff;
            margin-bottom: 20px;
        }

        .threshold-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .threshold-label {
            font-weight: 600;
            color: #aaa;
        }

        .threshold-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #00d4ff;
        }

        .activity-section {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        .activity-section h2 {
            color: #00d4ff;
            margin-bottom: 20px;
        }

        .activity-item {
            padding: 12px 15px;
            background: rgba(0, 0, 0, 0.3);
            border-left: 4px solid #00d4ff;
            margin-bottom: 10px;
            border-radius: 4px;
        }

        .activity-item.open {
            border-left-color: #00ff88;
            background: rgba(0, 255, 136, 0.1);
        }

        .activity-item.close {
            border-left-color: #ff4444;
            background: rgba(255, 68, 68, 0.1);
        }

        .activity-time {
            font-size: 0.85em;
            color: #aaa;
            margin-bottom: 5px;
        }

        .activity-text {
            font-weight: 600;
            color: #fff;
        }

        .refresh-info {
            text-align: center;
            color: white;
            margin-top: 20px;
            opacity: 0.8;
            font-size: 0.9em;
        }

        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }

        .status-active {
            background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
            color: #000;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
        }

        .status-idle {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: #000;
            box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Load Balancer Dashboard</h1>
            <p class="subtitle">Adaptive Threshold Learning & Decision Making</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Decisions</h3>
                <div class="value" id="total-decisions">0</div>
            </div>
            <div class="stat-card">
                <h3>Servers Opened</h3>
                <div class="value" id="total-opens" style="color: #00ff88;">0</div>
            </div>
            <div class="stat-card">
                <h3>Servers Closed</h3>
                <div class="value" id="total-closes" style="color: #ff4444;">0</div>
            </div>
            <div class="stat-card">
                <h3>Last Action</h3>
                <div class="value" id="last-action" style="font-size: 1.5em;">STAY</div>
            </div>
        </div>

        <div class="thresholds-section">
            <h2>🎯 AI Thresholds (Auto-Adjusted)</h2>
            <div class="threshold-row">
                <span class="threshold-label">Confidence Threshold</span>
                <span class="threshold-value" id="conf-threshold">0.700</span>
            </div>
            <div class="threshold-row">
                <span class="threshold-label">Idle Threshold (CPU %)</span>
                <span class="threshold-value" id="idle-threshold">5.0%</span>
            </div>
            <div class="threshold-row">
                <span class="threshold-label">Last Learning Time</span>
                <span class="threshold-value" id="last-learning" style="font-size: 1em;">Never</span>
            </div>
        </div>

        <div class="activity-section">
            <h2>📊 Recent Activity</h2>
            <div id="activity-log">
                <div class="activity-item">
                    <div class="activity-time">Waiting for AI decisions...</div>
                    <div class="activity-text">No activity yet</div>
                </div>
            </div>
        </div>

        <div class="refresh-info">
            Auto-refreshing every 2 seconds
        </div>
    </div>

    <script>
        let activityLog = [];

        async function fetchAIStatus() {
            try {
                const response = await fetch('/api/ai/status');
                if (!response.ok) throw new Error('Failed to fetch AI status');

                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to fetch AI data:', error);
            }
        }

        function updateDashboard(data) {
            // Update stats
            document.getElementById('total-decisions').textContent = data.total_decisions || 0;
            document.getElementById('total-opens').textContent = data.total_opens || 0;
            document.getElementById('total-closes').textContent = data.total_closes || 0;
            document.getElementById('last-action').textContent = data.last_action || 'STAY';

            // Update thresholds
            document.getElementById('conf-threshold').textContent = (data.conf_threshold || 0).toFixed(3);
            document.getElementById('idle-threshold').textContent = (data.idle_threshold || 0).toFixed(1) + '%';
            document.getElementById('last-learning').textContent = data.last_learning_time || 'Never';

            // Activity log would be updated here if we track it
        }

        // Initial fetch
        fetchAIStatus();

        // Auto-refresh every 2 seconds
        setInterval(fetchAIStatus, 2000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/ai/status')
def get_status():
    if ai_agent:
        dashboard_data['conf_threshold'] = ai_agent.brain.conf_threshold
        dashboard_data['idle_threshold'] = ai_agent.brain.idle_threshold
        dashboard_data['last_action'] = ai_agent.last_action

    return jsonify(dashboard_data)

def update_dashboard(action_type):
    """Update dashboard data when AI makes a decision"""
    dashboard_data['total_decisions'] += 1
    dashboard_data['last_decision_time'] = time.strftime('%H:%M:%S')

    if action_type == "OPEN_SERVER":
        dashboard_data['total_opens'] += 1
    elif action_type == "CLOSE_SERVER":
        dashboard_data['total_closes'] += 1

def run_flask_app():
    """Run Flask app in a separate thread"""
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Start Flask in background thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    print("="*50)
    print("  AI Dashboard running at http://localhost:5000")
    print("="*50)

    # Start AI agent
    ai_agent = AIProactiveAgent()
    ai_agent.start()
