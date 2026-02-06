import pandas as pd
import random
import os

LOCATIONS = {
    "Koramangala (Depot)": (12.9279, 77.6271),
    "Indiranagar": (12.9716, 77.6412),
    "Whitefield": (12.9698, 77.7500),
    "HSR Layout": (12.9121, 77.6446),
    "Electronic City": (12.8399, 77.6770),
    "Jayanagar": (12.9308, 77.5838),
    "Marathahalli": (12.9591, 77.6974),
    "Manyata Tech Park (Office)": (13.0500, 77.6150),
    "Bannerghatta (Far)": (12.8000, 77.5700) 
}

OFFICE_LAT, OFFICE_LON = LOCATIONS["Manyata Tech Park (Office)"]
DEPOT_LAT, DEPOT_LON = LOCATIONS["Koramangala (Depot)"]

def generate_tc05():
    # 1. Metadata
    metadata = [
        {"key": "allow_external_maps", "value": "False"},
        {"key": "priority_1_max_delay_min", "value": 5},
        {"key": "priority_2_max_delay_min", "value": 10},
        {"key": "priority_3_max_delay_min", "value": 15},
        {"key": "priority_4_max_delay_min", "value": 20},
        {"key": "priority_5_max_delay_min", "value": 30},
        {"key": "objective_cost_weight", "value": 0.7},
        {"key": "objective_time_weight", "value": 0.3}
    ]
    
    # 2. Vehicles (30 Total: 10 Large, 10 Med, 10 Small)
    vehicles = []
    # 10 SUVs (Cap 6)
    for i in range(10):
        vehicles.append({
            "vehicle_id": f"V_SUV_{i:02d}",
            "fuel_type": "Petrol",
            "vehicle_type": "SUV",
            "capacity": 6,
            "cost_per_km": 18.0,
            "avg_speed_kmph": 30,
            "current_lat": DEPOT_LAT,
            "current_lng": DEPOT_LON,
            "available_from": "08:00",
            "category": "SUV"
        })
    # 10 Sedans (Cap 4)
    for i in range(10):
        vehicles.append({
            "vehicle_id": f"V_SED_{i:02d}",
            "fuel_type": "Petrol",
            "vehicle_type": "Sedan",
            "capacity": 4,
            "cost_per_km": 14.0,
            "avg_speed_kmph": 30,
            "current_lat": DEPOT_LAT,
            "current_lng": DEPOT_LON,
            "available_from": "08:15",
            "category": "Sedan"
        })
    # 10 Hatchbacks (Cap 3)
    for i in range(10):
        vehicles.append({
            "vehicle_id": f"V_HAT_{i:02d}",
            "fuel_type": "Petrol",
            "vehicle_type": "Hatchback",
            "capacity": 3,
            "cost_per_km": 10.0,
            "avg_speed_kmph": 30,
            "current_lat": DEPOT_LAT,
            "current_lng": DEPOT_LON,
            "available_from": "08:30",
            "category": "Hatchback"
        })
        
    # 3. Employees (100 Requests)
    employees = []
    
    # Locations list for random sampling
    pickup_zones = ["Indiranagar", "Whitefield", "HSR Layout", "Electronic City", "Jayanagar", "Marathahalli"]
    
    for i in range(99): # 0 to 98 (Normal Cases)
        zone_name = random.choice(pickup_zones)
        base_lat, base_lon = LOCATIONS[zone_name]
        
        # Add random noise to spread within 2-3km
        p_lat = base_lat + random.uniform(-0.02, 0.02)
        p_lon = base_lon + random.uniform(-0.02, 0.02)
        
        prio = random.choices([1, 2, 3, 4, 5], weights=[10, 20, 40, 20, 10])[0]
        
        # Randomized windows around 9:30 AM (570m) - 10:30 AM (630m)
        drop_time = random.randint(570, 630) 
        drop_time_str = f"{drop_time // 60:02d}:{drop_time % 60:02d}"
        
        # Earliest pickup 1.5 hours before drop
        earliest_pickup = drop_time - 90
        earliest_str = f"{earliest_pickup // 60:02d}:{earliest_pickup % 60:02d}"
        
        employees.append({
            "employee_id": f"EMP_{i:03d}",
            "priority": prio,
            "pickup_lat": p_lat,
            "pickup_lng": p_lon,
            "drop_lat": OFFICE_LAT,
            "drop_lng": OFFICE_LON,
            "earliest_pickup": earliest_str,
            "latest_drop": drop_time_str,
            "vehicle_preference": "Any",
            "sharing_preference": "Any"
        })

    # --- Edge Case: EMP_99 ---
    # Live in Bannerghatta (Far South)
    # Be at Office (Far North) 25km+ away by 09:00 AM
    # Vehicles start at 08:30 in Koramangala (Middle)
    # This might fail because: 
    # Depot(8:30) -> Pickup(8:45?) -> Dropoff(9:00?) 
    # Distance is huge. Let's see if solver handles it or Forces it.
    bg_lat, bg_lon = LOCATIONS["Bannerghatta (Far)"]
    employees.append({
        "employee_id": "EMP_EDGE_99",
        "priority": 1, # High Priority, MUST reach
        "pickup_lat": bg_lat,
        "pickup_lng": bg_lon,
        "drop_lat": OFFICE_LAT,
        "drop_lng": OFFICE_LON,
        "earliest_pickup": "06:00", # Ready early
        "latest_drop": "09:00", # Tight deadline
        "vehicle_preference": "SUV", # Constrained
        "sharing_preference": "Any"
    })
    
    # Create DataFrame
    with pd.ExcelWriter("Velora Kriti_2026 TCs/TestCase_TC05.xlsx") as writer:
        pd.DataFrame(metadata).to_excel(writer, sheet_name="metadata", index=False)
        pd.DataFrame(vehicles).to_excel(writer, sheet_name="vehicles", index=False)
        pd.DataFrame(employees).to_excel(writer, sheet_name="employees", index=False)
        
    print("✓ Generated Velora Kriti_2026 TCs/TestCase_TC05.xlsx")

if __name__ == "__main__":
    generate_tc05()
