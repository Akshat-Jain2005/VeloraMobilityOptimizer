import pandas as pd
import os

files = [
    "Velora Kriti_2026 TCs/TestCase_TC01.xlsx",
    "Velora Kriti_2026 TCs/TestCase_TC02.xlsx",
    "Velora Kriti_2026 TCs/TestCase_TC03.xlsx",
    "Velora Kriti_2026 TCs/TestCase_TC04.xlsx"
]

for file_path in files:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
        
    print(f"--- {os.path.basename(file_path)} ---")
    try:
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
        
        # Check for Vehicles sheet
        vehicle_sheet = next((s for s in sheet_names if 'vehicle' in s.lower()), None)
        if vehicle_sheet:
            df_v = pd.read_excel(xls, sheet_name=vehicle_sheet)
            print(f"Vehicles columns ({vehicle_sheet}): {list(df_v.columns)}")
        else:
            print("Vehicles sheet not found.")

        # Check for Employees or Requests sheet
        emp_sheet = next((s for s in sheet_names if 'employee' in s.lower() or 'request' in s.lower()), None)
        if emp_sheet:
            df_e = pd.read_excel(xls, sheet_name=emp_sheet)
            print(f"Employees/Requests columns ({emp_sheet}): {list(df_e.columns)}")
        else:
             print("Employees/Requests sheet not found. Available sheets:", sheet_names)
             
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    print("\n")
