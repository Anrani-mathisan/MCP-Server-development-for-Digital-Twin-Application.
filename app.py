from flask import Flask, render_template, jsonify, request
# Import the custom control tools directly from your engine file
from digital_twin_server import get_twin_state, simulate_scenario, control_actuator

app = Flask(__name__)

@app.route('/')
def home():
    """Serves the main frontend dashboard screen."""
    return render_template('index.html')

@app.route('/api/state', methods=['GET'])
def api_get_state():
    """Returns the latest state with Autonomous Mitigation Logic injected."""
    state = get_twin_state()
    
    # 🤖 SMART LOGIC: Autonomous Mitigation Loop
    # We check the sensor state dynamically every time the UI requests data
    aqi_value = state['sensors']['air_quality']['value']
    
    if aqi_value > 100.0:
        # Automatically trigger hardware overrides if air quality degrades
        control_actuator('ventilation', 'speed', 'high')
        control_actuator('hvac', 'status', 'on')
        
        # Inject an active status flag so the frontend can display it
        state['automation_active'] = True
        state['automation_message'] = "🤖 AUTONOMOUS MITIGATION: High AQI detected. Max ventilation deployed."
    else:
        state['automation_active'] = False
        state['automation_message'] = ""
        
    return jsonify(state)

@app.route('/api/scenario', methods=['POST'])
def api_simulate_scenario():
    """Triggers the scenario profile updates safely, mapping the new midnight_eco profile."""
    data = request.get_json() or {}
    scenario_name = data.get('scenario', 'reset')
    
    # Check for dashboard reset buttons
    if scenario_name in ['', 'default', 'reset']:
        result_message = simulate_scenario('normal')
    else:
        # Securely dispatches 'midnight_eco', 'crowded', or 'fire_drill' to digital_twin_server.py
        result_message = simulate_scenario(scenario_name)
    
    # Grab the updated state data to return to the UI immediately
    current_state = get_twin_state()
    current_state['simulation_log'] = result_message
    return jsonify(current_state)

@app.route('/api/actuator', methods=['POST'])
def api_control_actuator():
    """Handles manual dashboard slider/button clicks to override hardware assets."""
    data = request.get_json() or {}
    name = data.get('name')
    setting = data.get('setting')
    value = data.get('value')
    
    result = control_actuator(name, setting, value)
    
    current_state = get_twin_state()
    current_state['simulation_log'] = result
    return jsonify(current_state)

if __name__ == '__main__':
    print("Flask Digital Twin Dashboard starting at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)