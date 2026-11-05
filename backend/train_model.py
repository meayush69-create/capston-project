import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import classification_report, mean_squared_error, r2_score

# 1. Feature Engineering
def engineer_features(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['asset_id', 'timestamp']).reset_index(drop=True)
    
    # Rolling trend indicators (over 4-step = 1-hour window)
    for col in ['vibration_rms_mms', 'internal_temp_c', 'power_kw']:
        df[f'{col}_roll_mean'] = df.groupby('asset_id')[col].transform(lambda x: x.rolling(4, min_periods=1).mean())
        df[f'{col}_roll_std'] = df.groupby('asset_id')[col].transform(lambda x: x.rolling(4, min_periods=1).std().fillna(0))
    
    # Delta temperature
    df['temp_gradient'] = df['internal_temp_c'] - df['ambient_temp_c']
    return df

def run_training():
    df = pd.read_csv("smart_campus_iot_telemetry.csv")
    df = engineer_features(df)
    
    features = [
        'ambient_temp_c', 'internal_temp_c', 'vibration_rms_mms',
        'acoustic_db', 'pressure_psi', 'power_kw', 'campus_occupancy_flag',
        'vibration_rms_mms_roll_mean', 'vibration_rms_mms_roll_std',
        'internal_temp_c_roll_mean', 'internal_temp_c_roll_std',
        'power_kw_roll_mean', 'power_kw_roll_std', 'temp_gradient'
    ]
    
    X = df[features]
    y_class = df['failure_risk_binary']
    
    # Filter dataset for RUL regression on active degradation cycles
    degrading_mask = df['rul_hours'] < 500.0
    X_reg = df.loc[degrading_mask, features]
    y_reg = df.loc[degrading_mask, 'rul_hours']
    
    # Train/Val Split
    X_train_c, X_val_c, y_train_c, y_val_c = train_test_split(X, y_class, test_size=0.2, random_state=42, stratify=y_class)
    X_train_r, X_val_r, y_train_r, y_val_r = train_test_split(X_reg, y_reg, test_size=0.2, random_state=42)
    
    # Failure Risk Classification Model
    clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    clf.fit(X_train_c, y_train_c)
    preds_c = clf.predict(X_val_c)
    print("=== Classification Model Report (Failure Risk) ===")
    print(classification_report(y_val_c, preds_c))
    
    # RUL Regressor
    reg = GradientBoostingRegressor(n_estimators=120, max_depth=5, learning_rate=0.08, random_state=42)
    reg.fit(X_train_r, y_train_r)
    preds_r = reg.predict(X_val_r)
    print("=== RUL Regressor Report ===")
    print(f"R² Score: {r2_score(y_val_r, preds_r):.4f}")
    print(f"RMSE: {np.sqrt(mean_squared_error(y_val_r, preds_r)):.2f} hours")
    
    # Save artifacts
    joblib.dump(clf, "failure_classifier.pkl")
    joblib.dump(reg, "rul_regressor.pkl")
    joblib.dump(features, "feature_columns.pkl")
    print("Models and artifacts saved successfully.")

if __name__ == "__main__":
    run_training()