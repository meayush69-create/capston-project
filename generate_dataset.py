import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_campus_iot_data(n_days=90, interval_mins=15, seed=42):
    np.random.seed(seed)
    total_steps = (n_days * 24 * 60) // interval_mins
    start_time = datetime(2026, 1, 1, 0, 0)
    timestamps = [start_time + timedelta(minutes=i * interval_mins) for i in range(total_steps)]
    
    asset_configs = {
        "HVAC_Chiller_01": {"type": "HVAC", "base_power": 45.0, "fail_at_step": int(total_steps * 0.72)},
        "HVAC_Chiller_02": {"type": "HVAC", "base_power": 42.0, "fail_at_step": None},
        "Water_Pump_Central": {"type": "Pump", "base_power": 18.0, "fail_at_step": int(total_steps * 0.45)},
        "Elevator_Tower_A": {"type": "Elevator", "base_power": 25.0, "fail_at_step": int(total_steps * 0.88)},
    }
    
    records = []
    
    for asset_id, config in asset_configs.items():
        fail_step = config["fail_at_step"]
        
        for step, ts in enumerate(timestamps):
            hour = ts.hour
            # Diurnal temperature cycle (18°C to 34°C)
            ambient_temp = 24.0 + 8.0 * np.sin(2 * np.pi * (hour - 9) / 24) + np.random.normal(0, 0.6)
            
            # Operational load based on campus working hours (8:00 - 18:00)
            is_active_hours = 1 if 8 <= hour <= 18 else 0
            base_load = 1.0 if is_active_hours else 0.35
            
            # Progressive degradation factor
            wear_factor = 0.0
            if fail_step is not None:
                start_degrade = max(0, fail_step - 800)
                if step >= start_degrade:
                    progress = (step - start_degrade) / (fail_step - start_degrade)
                    wear_factor = min(1.0, progress)
            
            # Sensor telemetry physics
            vibration_rms = 1.2 + (wear_factor ** 2) * 5.8 + np.random.normal(0, 0.15)
            internal_temp = 40.0 + (wear_factor * 35.0) + (ambient_temp * 0.4) + np.random.normal(0, 0.8)
            power_draw_kw = config["base_power"] * (base_load + wear_factor * 0.35) + np.random.normal(0, 1.2)
            acoustic_db = 55.0 + (wear_factor * 28.0) + np.random.normal(0, 1.5)
            flow_pressure_psi = 60.0 - (wear_factor * 22.0) + np.random.normal(0, 1.0)
            
            # Failure label and RUL calculation
            is_failed = 1 if (fail_step is not None and step >= fail_step) else 0
            if fail_step is not None:
                rul_steps = max(0, fail_step - step)
                rul_hours = (rul_steps * interval_mins) / 60.0
            else:
                rul_hours = 9999.0  # Healthy baseline
            
            records.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "asset_id": asset_id,
                "asset_type": config["type"],
                "ambient_temp_c": round(ambient_temp, 2),
                "internal_temp_c": round(internal_temp, 2),
                "vibration_rms_mms": round(max(0.1, vibration_rms), 3),
                "acoustic_db": round(acoustic_db, 2),
                "pressure_psi": round(max(5.0, flow_pressure_psi), 2),
                "power_kw": round(max(1.0, power_draw_kw), 2),
                "campus_occupancy_flag": is_active_hours,
                "rul_hours": round(rul_hours, 2),
                "failure_risk_binary": 1 if wear_factor > 0.65 else 0,
                "failed": is_failed
            })
            
    df = pd.DataFrame(records)
    df.to_csv("smart_campus_iot_telemetry.csv", index=False)
    print(f"Dataset generated: {len(df)} records saved to 'smart_campus_iot_telemetry.csv'")
    return df

if __name__ == "__main__":
    generate_campus_iot_data()