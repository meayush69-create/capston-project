import streamlit as st
import pandas as pd
import plotly.express as px
from digital_twin_engine import CampusAssetDigitalTwin

st.set_page_config(page_title="Campus Digital Twin", layout="wide")
st.title("🏛️ Smart CU Campus Infrastructure — AI Digital Twin")

@st.cache_data
def load_data():
    return pd.read_csv("smart_campus_iot_telemetry.csv")

df = load_data()
selected_asset = st.sidebar.selectbox("Select Campus Asset", df['asset_id'].unique())
asset_df = df[df['asset_id'] == selected_asset].copy()

# Latest state snapshot
latest = asset_df.iloc[-1]
twin = CampusAssetDigitalTwin(selected_asset, latest['asset_type'], latest['power_kw'])
state = twin.process_telemetry(latest.to_dict())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Health Score", f"{state['health_score']}%")
col2.metric("Operational Status", state['status'])
col3.metric("Failure Risk", f"{state['failure_probability'] * 100:.1f}%")
col4.metric("Estimated RUL", f"{state['estimated_rul_hours']} hrs")

st.info(f"**Automated Directive:** {state['action']} | **Energy Mode:** `{state['energy_mode']}`")

# Time-series charts
col_left, col_right = st.columns(2)
with col_left:
    fig_vib = px.line(asset_df, x='timestamp', y='vibration_rms_mms', title="Vibration RMS (mm/s)")
    st.plotly_chart(fig_vib, use_container_width=True)
with col_right:
    fig_temp = px.line(asset_df, x='timestamp', y=['internal_temp_c', 'ambient_temp_c'], title="Thermal Profile (°C)")
    st.plotly_chart(fig_temp, use_container_width=True)