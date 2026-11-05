import joblib
import pandas as pd
import numpy as np

class CampusAssetDigitalTwin:
    def __init__(self, asset_id, asset_type, baseline_power):
        self.asset_id = asset_id
        self.asset_type = asset_type
        self.baseline_power = baseline_power
        
        # Load pre-trained AI assets
        self.classifier = joblib.load("failure_classifier.pkl")
        self.rul_regressor = joblib.load("rul_regressor.pkl")
        self.features = joblib.load("feature_columns.pkl")
        
        # Twin State
        self.telemetry_history = []
        self.health_score = 100.0  # 0 to 100 scale
        self.status = "HEALTHY"
        self.recommended_action = "Routine Operation"
        self.energy_optimization_mode = "STANDARD"

    def process_telemetry(self, raw_reading: dict):
        self.telemetry_history.append(raw_reading)
        if len(self.telemetry_history) > 10:
            self.telemetry_history.pop(0)
            
        history_df = pd.DataFrame(self.telemetry_history)
        
        # Compute real-time engineered features
        current = raw_reading.copy()
        current['temp_gradient'] = current['internal_temp_c'] - current['ambient_temp_c']
        
        for metric in ['vibration_rms_mms', 'internal_temp_c', 'power_kw']:
            current[f'{metric}_roll_mean'] = history_df[metric].tail(4).mean()
            current[f'{metric}_roll_std'] = history_df[metric].tail(4).std() if len(history_df) >= 2 else 0.0
            
        feat_vector = pd.DataFrame([[current[f] for f in self.features]], columns=self.features)
        
        # AI Inference
        risk_probability = self.classifier.predict_proba(feat_vector)[0][1]
        predicted_rul = float(self.rul_regressor.predict(feat_vector)[0])
        
        # Update Digital Twin Dynamics
        self.health_score = max(0.0, 100.0 - (risk_probability * 80.0) - max(0.0, (150.0 - predicted_rul) * 0.15))
        
        # Energy and Maintenance Decision Engine
        if risk_probability > 0.65 or self.health_score < 40.0:
            self.status = "CRITICAL"
            self.recommended_action = "Dispatch immediate field inspection; shift load to redundant unit."
            self.energy_optimization_mode = "DERATED_ECO" # Throttle to prevent catastrophic failure
        elif risk_probability > 0.35 or self.health_score < 70.0:
            self.status = "WARNING"
            self.recommended_action = "Schedule maintenance during upcoming off-peak campus hours."
            self.energy_optimization_mode = "LOAD_BALANCED"
        else:
            self.status = "HEALTHY"
            self.recommended_action = "Standard autonomous monitoring."
            self.energy_optimization_mode = "CAMPUS_EFFICIENCY_OPTIMIZED"

        return {
            "asset_id": self.asset_id,
            "health_score": round(self.health_score, 1),
            "status": self.status,
            "failure_probability": round(risk_probability, 3),
            "estimated_rul_hours": round(predicted_rul, 1) if predicted_rul < 500 else "> 500",
            "energy_mode": self.energy_optimization_mode,
            "action": self.recommended_action
        }

# Simulated Runtime Demonstration
if __name__ == "__main__":
    twin = CampusAssetDigitalTwin("HVAC_Chiller_01", "HVAC", 45.0)
    
    # Degraded sensor snapshot simulation
    test_reading = {
        "ambient_temp_c": 32.5,
        "internal_temp_c": 68.4,
        "vibration_rms_mms": 4.82,
        "acoustic_db": 78.1,
        "pressure_psi": 42.0,
        "power_kw": 54.3,
        "campus_occupancy_flag": 1
    }
    
    state_report = twin.process_telemetry(test_reading)
    print("\n--- Digital Twin State Report ---")
    for k, v in state_report.items():
        print(f"{k:<25}: {v}")