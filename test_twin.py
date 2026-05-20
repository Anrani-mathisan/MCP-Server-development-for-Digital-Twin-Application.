# test_twin.py
import json
from digital_twin_server import get_twin_state, simulate_scenario, get_alerts

print("--- STEP 1: INITIAL STATE ---")
print(json.dumps(get_twin_state(), indent=2))

print("\n--- STEP 2: SIMULATING CROWDED SCENARIO ---")
print(simulate_scenario("crowded"))

print("\n--- STEP 3: CHECKING ALERT ENGINE ---")
print(get_alerts())