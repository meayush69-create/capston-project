import time
import pandas as pd
from digital_twin_engine import CampusAssetDigitalTwin

def run_campus_simulation(csv_path="smart_campus_iot_telemetry.csv", delay_sec=1.0):
    df = pd.read_csv(csv_path)
    
    # Initialize Digital Twins for all distinct assets
    asset_types = {
        "HVAC_Chiller_01": ("HVAC", 45.0),
        "HVAC_Chiller_02": ("HVAC", 42.0),
        "Water_Pump_Central": ("Pump", 18.0),
        "Elevator_Tower_A": ("Elevator", 25.0)
    }
    
    twins = {
        asset_id: CampusAssetDigitalTwin(asset_id, atype, base_p)
        for asset_id, (atype, base_p) in asset_types.items()
    }
    
    print("=" * 80)
    print("🚀 SMART CAMPUS DIGITAL TWIN MONITORING SERVICE STARTED")
    print("=" * 80)

    # Replay degradation sequences step by step
    unique_timestamps = df['timestamp'].unique()
    
    for ts in unique_timestamps[::8]:  # Sample every 2 hours of telemetry
        current_slice = df[df['timestamp'] == ts]
        print(f"\n🕒 Timestamp: {ts}")
        print(f"{'Asset ID':<22} | {'Health':<7} | {'Status':<10} | {'Risk':<6} | {'RUL (hrs)':<10} | {'Mode'}")
        print("-" * 80)
        
        for _, row in current_slice.iterrows():
            aid = row['asset_id']
            if aid not in twins:
                continue
                
            raw_reading = {
                "ambient_temp_c": row['ambient_temp_c'],
                "internal_temp_c": row['internal_temp_c'],
                "vibration_rms_mms": row['vibration_rms_mms'],
                "acoustic_db": row['acoustic_db'],
                "pressure_psi": row['pressure_psi'],
                "power_kw": row['power_kw'],
                "campus_occupancy_flag": row['campus_occupancy_flag']
            }
            
            report = twins[aid].process_telemetry(raw_reading)
            rul_display = str(report['estimated_rul_hours'])
            print(f"{aid:<22} | {report['health_score']:<7.1f} | {report['status']:<10} | {report['failure_probability']:<6.2f} | {rul_display:<10} | {report['energy_mode']}")
            
        time.sleep(delay_sec)

if __name__ == "__main__":
    run_campus_simulation()