#!/usr/bin/env python3
"""Simple Excel to JSON converter for Velora optimizer.

Usage: python parser/excel_to_json.py input.xlsx output.json

Expected sheets (optional): vehicles, requests, employees (not required)

"""
import sys
import json
import pandas as pd
from datetime import datetime

def sheet_to_records(df):
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient='records')

def time_to_minutes(time_obj):
    """Convert time object or string (HH:MM) to minutes since midnight."""
    import datetime as dt
    if isinstance(time_obj, dt.time):
        return time_obj.hour * 60 + time_obj.minute
    elif isinstance(time_obj, str):
        try:
            h, m = time_obj.split(':')
            return int(h) * 60 + int(m)
        except:
            return 0.0
    elif isinstance(time_obj, (int, float)):
        return float(time_obj)
    return 0.0

def main():
    if len(sys.argv) < 3:
        print("Usage: excel_to_json.py input.xlsx output.json")
        return
    inp = sys.argv[1]
    out = sys.argv[2]
    xls = pd.ExcelFile(inp)
    result = {"config": {"allow_external_maps": False, "maps_api_key": ""}}

    if 'vehicles' in xls.sheet_names:
        df = xls.parse('vehicles')
        vehicles = []
        for idx, r in enumerate(sheet_to_records(df)):
            v = {
                'id': idx,
                'vehicle_id': r.get('vehicle_id', f'V{idx:02d}'),
                'capacity': int(r.get('capacity', 4)),
                'costPerKm': float(r.get('cost_per_km', r.get('costPerKm', 1.0))),
                'startLoc': {'lat': float(r.get('current_lat', r.get('startLat', 0.0))), 
                            'lon': float(r.get('current_lng', r.get('startLon', 0.0)))},
                'availabilityTime': time_to_minutes(r.get('available_from', r.get('availabilityTime', 0.0)))
            }
            vehicles.append(v)
        result['vehicles'] = vehicles

    if 'employees' in xls.sheet_names:
        df = xls.parse('employees')
        # Employees map to requests (trips)
        reqs = []
        for idx, r in enumerate(sheet_to_records(df)):
            req = {
                'id': idx,
                'employee_id': r.get('employee_id', f'E{idx:02d}'),
                'priority': int(r.get('priority', 3)),
                'pickup': {'lat': float(r.get('pickup_lat', r.get('pickupLat', 0.0))), 
                          'lon': float(r.get('pickup_lng', r.get('pickupLon', 0.0)))},
                'dropoff': {'lat': float(r.get('drop_lat', r.get('dropoffLat', 0.0))), 
                           'lon': float(r.get('drop_lng', r.get('dropoffLon', 0.0)))},
                'earlyTime': time_to_minutes(r.get('earliest_pickup', r.get('earlyTime', 0.0))),
                'lateTime': time_to_minutes(r.get('latest_drop', r.get('lateTime', 1e6))),
                'load': int(r.get('load', r.get('Load', 1)))
            }
            reqs.append(req)
        result['requests'] = reqs
    elif 'requests' in xls.sheet_names:
        df = xls.parse('requests')
        reqs = []
        for r in sheet_to_records(df):
            req = {
                'id': int(r.get('id', 0)),
                'priority': int(r.get('priority', 3)),
                'pickup': {'lat': float(r.get('pickupLat', 0.0)), 'lon': float(r.get('pickupLon', 0.0))},
                'dropoff': {'lat': float(r.get('dropoffLat', 0.0)), 'lon': float(r.get('dropoffLon', 0.0))},
                'earlyTime': float(r.get('earlyTime', 0.0)),
                'lateTime': float(r.get('lateTime', 1e6)),
                'load': int(r.get('load', 1))
            }
            reqs.append(req)
        result['requests'] = reqs

    if 'employees' in xls.sheet_names:
        df = xls.parse('employees')
        emps = []
        for r in sheet_to_records(df):
            e = {
                'id': int(r.get('id', 0)),
                'name': r.get('name', ''),
                'shiftStart': float(r.get('shiftStart', 0.0)),
                'shiftEnd': float(r.get('shiftEnd', 24.0)),
                'startLoc': {'lat': float(r.get('startLat', 0.0)), 'lon': float(r.get('startLon', 0.0))}
            }
            emps.append(e)
        result['employees'] = emps

    # Generic fallback: try to read first sheet as requests if none found
    if 'requests' not in result and 'vehicles' not in result:
        df = xls.parse(xls.sheet_names[0])
        result['requests'] = []
        for r in sheet_to_records(df):
            # expect columns named pickupLat,pickupLon,dropoffLat,dropoffLon
            if all(k in r for k in ('pickupLat','pickupLon','dropoffLat','dropoffLon')):
                req = {
                    'id': int(r.get('id', 0)),
                    'priority': int(r.get('priority', 3)),
                    'pickup': {'lat': float(r.get('pickupLat', 0.0)), 'lon': float(r.get('pickupLon', 0.0))},
                    'dropoff': {'lat': float(r.get('dropoffLat', 0.0)), 'lon': float(r.get('dropoffLon', 0.0))},
                    'earlyTime': float(r.get('earlyTime', 0.0)),
                    'lateTime': float(r.get('lateTime', 1e6)),
                    'load': int(r.get('load', 1))
                }
                result['requests'].append(req)

    # Extract baseline costs if available
    if 'baseline' in xls.sheet_names:
        df = xls.parse('baseline')
        baseline_data = sheet_to_records(df)
        result['baseline'] = baseline_data

    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print('Wrote', out)

if __name__ == '__main__':
    main()
