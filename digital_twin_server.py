import sys
import random
from datetime import datetime
from typing import Optional
from fastmcp import FastMCP

# 1. Initialize the MCP Server
mcp = FastMCP("Smart-Room-Digital-Twin")

# 2. In-Memory State Store with active_scenario tracking
twin_state = {
    "room_name": "Smart Lab Room A1",
    "location": "Building 3, Floor 2",
    "last_updated": datetime.now().isoformat(),
    "active_scenario": "normal",
    "sensors": {
        "temperature": { "value": 22.5, "unit": "°C", "min": 15.0, "max": 40.0, "alert_min": 18.0, "alert_max": 30.0 },
        "humidity": { "value": 45.0, "unit": "%", "min": 10.0, "max": 90.0, "alert_min": 30.0, "alert_max": 80.0 },
        "air_quality": { "value": 42.0, "unit": "AQI", "min": 0.0, "max": 300.0, "alert_max": 150.0 },
        "occupancy": { "value": 4.0, "unit": "people", "min": 0.0, "max": 50.0, "alert_max": 25.0 }
    },
    "actuators": {
        "hvac": { "status": "on", "mode": "cooling", "setpoint": 22.0 },
        "lighting": { "status": "on", "brightness": 75 },
        "ventilation": { "status": "on", "speed": "medium" }
    },
    "alerts": [],
    "history": []
}

# --- HELPER UTILITIES ---

def log_event(event_type: str, description: str):
    """Adds a timestamped event to a circular buffer of 50 items."""
    history = twin_state["history"]
    if len(history) >= 50: 
        history.pop(0)
    history.append({
        "timestamp": datetime.now().isoformat(), 
        "type": event_type, 
        "description": description
    })

def evaluate_alerts():
    """Validates sensors against defined thresholds."""
    current_alerts = []
    sensors = twin_state["sensors"]
    
    t = sensors["temperature"]
    if t["value"] < t["alert_min"]: current_alerts.append(f"CRITICAL: Low Temperature ({t['value']}°C)")
    elif t["value"] > t["alert_max"]: current_alerts.append(f"CRITICAL: High Temperature ({t['value']}°C)")
        
    h = sensors["humidity"]
    if h["value"] < h["alert_min"]: current_alerts.append(f"WARNING: Low Humidity ({h['value']}%)")
    elif h["value"] > h["alert_max"]: current_alerts.append(f"WARNING: High Humidity ({h['value']}%)")
        
    aq = sensors["air_quality"]
    if aq["value"] > aq["alert_max"]: current_alerts.append(f"CRITICAL: Poor Air Quality ({aq['value']} AQI)")
        
    occ = sensors["occupancy"]
    if occ["value"] > occ["alert_max"]: current_alerts.append(f"WARNING: Overcrowded ({int(occ['value'])} people)")
        
    twin_state["alerts"] = current_alerts

def simulate_drift():
    """Gaussian Random Drift and Closed-Loop Physics Simulation Model."""
    sensors = twin_state["sensors"]
    actuators = twin_state["actuators"]
    active_scenario = twin_state.get("active_scenario", "normal")
    
    # 1. Scenario-specific target profiles
    if active_scenario == "normal":
        target_occ = 4.0
        target_temp = 22.5
        target_humidity = 45.0
        target_aqi = 42.0
    elif active_scenario == "crowded":
        target_occ = 35.0
        target_temp = 29.0
        target_humidity = 65.0
        target_aqi = 145.0
    elif active_scenario == "fire_drill":
        target_occ = 0.0
        target_temp = 55.0
        target_humidity = 30.0
        target_aqi = 250.0
    elif active_scenario == "midnight_eco":
        target_occ = 0.0
        target_temp = 25.0
        target_humidity = 50.0
        target_aqi = 30.0
    else:
        target_occ = 4.0
        target_temp = 22.5
        target_humidity = 45.0
        target_aqi = 42.0

    # 2. Occupancy adjustments
    sensors["occupancy"]["value"] = float(target_occ)

    # 3. Add Ambient Drift / Gaussian Noise
    temp_noise = random.gauss(0, 0.05)
    humidity_noise = random.gauss(0, 0.1)
    aqi_noise = random.gauss(0, 0.2)

    # 4. Closed-loop feedback physics from Actuators
    # HVAC logic
    hvac = actuators["hvac"]
    if hvac["status"] == "on":
        setpoint = hvac.get("setpoint", 22.0)
        temp_diff = setpoint - sensors["temperature"]["value"]
        temp_adjustment = temp_diff * 0.1
    else:
        # Slow drift towards target scenario temp
        temp_diff = target_temp - sensors["temperature"]["value"]
        temp_adjustment = temp_diff * 0.02
    sensors["temperature"]["value"] += temp_adjustment + temp_noise
    sensors["temperature"]["value"] = max(sensors["temperature"]["min"], 
                                          min(sensors["temperature"]["max"], 
                                              sensors["temperature"]["value"]))

    # Ventilation logic on AQI
    vent = actuators["ventilation"]
    if vent["status"] == "on":
        if vent["speed"] == "high":
            aqi_adjustment = -3.0
        elif vent["speed"] == "medium":
            aqi_adjustment = -1.5
        else:
            aqi_adjustment = -0.5
    else:
        # Drift towards target AQI
        aqi_adjustment = (target_aqi - sensors["air_quality"]["value"]) * 0.05

    # Scenario impact
    if active_scenario == "crowded":
        aqi_adjustment += 2.0
    elif active_scenario == "fire_drill":
        aqi_adjustment += 10.0
        
    sensors["air_quality"]["value"] += aqi_adjustment + aqi_noise
    sensors["air_quality"]["value"] = max(sensors["air_quality"]["min"], 
                                          min(sensors["air_quality"]["max"], 
                                              sensors["air_quality"]["value"]))

    # Humidity logic
    humidity_adjustment = (target_humidity - sensors["humidity"]["value"]) * 0.02
    if hvac["status"] == "on" and hvac.get("mode") == "cooling":
        humidity_adjustment -= 0.2  # Dehumidification from AC
    sensors["humidity"]["value"] += humidity_adjustment + humidity_noise
    sensors["humidity"]["value"] = max(sensors["humidity"]["min"], 
                                        min(sensors["humidity"]["max"], 
                                            sensors["humidity"]["value"]))
    
    # 5. 🤖 AUTONOMOUS MITIGATION LOGIC (Traceable Self-Healing)
    now_str = datetime.now().strftime('%H:%M:%S')

    # Air Quality mitigation
    if sensors["air_quality"]["value"] > 100.0 and actuators["ventilation"]["speed"] != "high":
        actuators["ventilation"]["status"] = "on"
        actuators["ventilation"]["speed"] = "high"
        log_event("AUTO_SYSTEM", f"MITIGATION: High AQI ({sensors['air_quality']['value']:.1f}) detected. Fans set to HIGH at {now_str}.")
    
    # Temperature mitigation
    if sensors["temperature"]["value"] > 27.0 and actuators["hvac"]["status"] == "off":
        actuators["hvac"]["status"] = "on"
        actuators["hvac"]["mode"] = "cooling"
        log_event("AUTO_SYSTEM", f"MITIGATION: High Temp ({sensors['temperature']['value']:.1f}°C) detected. Cooling enabled at {now_str}.")
    
    # Empty Room mitigation
    if sensors["occupancy"]["value"] == 0 and actuators["lighting"]["status"] == "on":
        actuators["lighting"]["status"] = "off"
        actuators["lighting"]["brightness"] = 0
        log_event("AUTO_SYSTEM", f"ENERGY SAVING: Room vacant. Lights off at {now_str}.")

    # Evaluate everything
    evaluate_alerts()

# --- MCP TOOLS & EXPORTED APIs ---

@mcp.tool()
def get_twin_state() -> dict:
    """Returns the complete digital twin state structure."""
    simulate_drift()
    twin_state["last_updated"] = datetime.now().isoformat()
    return twin_state

@mcp.tool()
def simulate_scenario(scenario: str) -> str:
    """Configures the digital twin to run a specified preset scenario profile.
    
    Accepts: 'normal', 'crowded', 'fire_drill', or 'midnight_eco'.
    """
    if scenario not in ["normal", "crowded", "fire_drill", "midnight_eco"]:
        return f"Unknown scenario: {scenario}"
    
    twin_state["active_scenario"] = scenario
    
    sensors = twin_state["sensors"]
    actuators = twin_state["actuators"]
    
    if scenario == "normal":
        sensors["occupancy"]["value"] = 4.0
        sensors["temperature"]["value"] = 22.5
        sensors["humidity"]["value"] = 45.0
        sensors["air_quality"]["value"] = 42.0
        actuators["hvac"]["status"] = "on"
        actuators["lighting"]["status"] = "on"
        actuators["lighting"]["brightness"] = 75
        actuators["ventilation"]["status"] = "on"
        actuators["ventilation"]["speed"] = "medium"
        log_event("SCENARIO", "Scenario reset to Normal defaults.")
        return "Scenario configured to 'normal'."
        
    elif scenario == "crowded":
        sensors["occupancy"]["value"] = 35.0
        sensors["air_quality"]["value"] = 120.0
        log_event("SCENARIO", "Scenario configured to Crowded Smart-Room.")
        return "Scenario configured to 'crowded'."
        
    elif scenario == "fire_drill":
        sensors["occupancy"]["value"] = 0.0
        sensors["temperature"]["value"] = 40.0
        sensors["air_quality"]["value"] = 180.0
        actuators["hvac"]["status"] = "off"
        log_event("SCENARIO", "CRITICAL: Fire Drill initiated.")
        return "Scenario configured to 'fire_drill'."
        
    elif scenario == "midnight_eco":
        sensors["occupancy"]["value"] = 0.0
        sensors["temperature"]["value"] = 24.5
        actuators["lighting"]["status"] = "off"
        actuators["lighting"]["brightness"] = 0
        actuators["ventilation"]["status"] = "off"
        log_event("SCENARIO", "Scenario configured to Midnight Eco-saving.")
        return "Scenario configured to 'midnight_eco'."

@mcp.tool()
def control_actuator(name: str, setting: str, value: str) -> str:
    """Manually overrides an actuator's target parameters.
    
    Accepts:
      name: 'hvac', 'lighting', or 'ventilation'
      setting: 'status', 'mode', 'setpoint', 'brightness', or 'speed'
      value: string value (e.g. 'on', 'off', 'high', 'cooling', '22.5', '75')
    """
    actuators = twin_state["actuators"]
    if name not in actuators:
        return f"Error: Actuator '{name}' not found."
    
    actuator = actuators[name]
    
    # Standardize true/on/false/off
    if value.lower() in ["on", "true"]:
        typed_value = "on"
    elif value.lower() in ["off", "false"]:
        typed_value = "off"
    else:
        try:
            if "." in value:
                typed_value = float(value)
            else:
                typed_value = int(value)
        except ValueError:
            typed_value = value
            
    if setting in actuator:
        actuator[setting] = typed_value
    else:
        # Fallback dynamic injection
        actuator[setting] = typed_value
        
    msg = f"Manual override: Set {name} {setting} to {typed_value}."
    log_event("MANUAL_OVERRIDE", msg)
    evaluate_alerts()
    return msg

@mcp.tool()
def get_alerts() -> list:
    """Returns the list of active alerts generated by thresholds."""
    evaluate_alerts()
    return twin_state["alerts"]

@mcp.tool()
def read_sensor(sensor_name: str) -> dict:
    """Reads details and current telemetry of a specified sensor."""
    sensors = twin_state["sensors"]
    if sensor_name not in sensors:
        raise ValueError(f"Sensor '{sensor_name}' not found.")
    return sensors[sensor_name]

@mcp.tool()
def update_sensor(sensor_name: str, value: float) -> str:
    """Directly sets a sensor value (useful for simulating external telemetry inputs)."""
    sensors = twin_state["sensors"]
    if sensor_name not in sensors:
        return f"Error: Sensor '{sensor_name}' not found."
    sensors[sensor_name]["value"] = value
    evaluate_alerts()
    return f"Sensor '{sensor_name}' updated to {value}."

if __name__ == "__main__":
    mcp.run(transport="stdio")