import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

# ================== PAGE CONFIG ==================
st.set_page_config(
    page_title="DAST Security Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# ================== DARK MODE STYLES ==================
st.markdown("""
<style>
body { background-color: #0E1117; color: #FAFAFA; }
.stApp { background-color: #0E1117; }
table, th, td { color: #FAFAFA !important; }
</style>
""", unsafe_allow_html=True)

# ================== HEADER ==================
st.title("🛡️ DAST Security Dashboard")
st.caption("SpaceX Explorer API – Dark Mode SOC-style Dashboard")
st.markdown("---")

# ================== LOAD DATA ==================
with open("dast_results.json") as f:
    df = pd.DataFrame(json.load(f))

# ================== SEVERITY LOGIC ==================
def calculate_severity(row):
    if row["status_code"] == 200:
        return "Low"
    if row["attack_type"] in ["sql_injection", "xss"]:
        return "High"
    return "Medium"

df["severity"] = df.apply(calculate_severity, axis=1)

# ================== EXECUTIVE KPIS ==================
st.subheader("📌 Executive Summary")
total_requests = len(df)
issues = df[df["status_code"] != 200]
error_rate = round((len(issues)/total_requests)*100,2)
high_risk_count = len(df[df["severity"]=="High"])
medium_risk_count = len(df[df["severity"]=="Medium"])
low_risk_count = len(df[df["severity"]=="Low"])
unique_endpoints = df["endpoint"].nunique()

kpi_cols = st.columns(5)
kpi_cols[0].metric("🔎 Requests Sent", total_requests)
kpi_cols[1].metric("⚠️ Anomalies Detected", len(issues))
kpi_cols[2].metric("📉 Error Ratio (%)", f"{error_rate}")
kpi_cols[3].metric("🟥 High Risk", high_risk_count)
kpi_cols[4].metric("🟡 Medium Risk", medium_risk_count)

st.markdown("---")

# ================== ATTACK COVERAGE ==================
st.subheader("🎯 Attack Coverage")

attack_counts = df["attack_type"].value_counts().rename_axis("Attack Type").reset_index(name="Count")
fig_attack = px.bar(
    attack_counts,
    x="Attack Type",
    y="Count",
    color="Attack Type",
    text="Count",
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Vivid
)
fig_attack.update_layout(showlegend=False)
st.plotly_chart(fig_attack, use_container_width=True)

# ================== API RESPONSE HEALTH ==================
st.subheader("📡 API Response Behavior")
status_counts = df["status_code"].astype(str).value_counts().rename_axis("HTTP Status").reset_index(name="Count")
fig_status = px.bar(
    status_counts,
    x="HTTP Status",
    y="Count",
    text="Count",
    template="plotly_dark",
    color="HTTP Status",
    color_discrete_map={"200":"#00FF9D","400":"#FFB300","404":"#FF6B6B","500":"#FF0000"}
)
st.plotly_chart(fig_status, use_container_width=True)

# ================== SEVERITY GAUGE ==================
st.subheader("🚦 Severity Ratio")
severity_ratio = round(len(df[df["severity"]=="High"])/total_requests*100,1)
fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number+delta",
    value = severity_ratio,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "High Severity Requests (%)"},
    gauge = {
        'axis': {'range': [0, 100]},
        'bar': {'color': "#FF4C4C"},
        'steps': [
            {'range': [0, 20], 'color': "#00FF9D"},
            {'range': [20, 50], 'color': "#FFB300"},
            {'range': [50, 100], 'color': "#FF4C4C"},
        ],
    }
))
st.plotly_chart(fig_gauge, use_container_width=True)

# ================== ENDPOINT RISK TABLE ==================
st.subheader("🚨 Endpoint Risk Overview")
risk_table = df.groupby("endpoint").agg(
    Total_Attempts=("endpoint","count"),
    Issues=("status_code", lambda x: (x!=200).sum()),
    High_Risk=("severity", lambda x: (x=="High").sum())
).reset_index().sort_values("High_Risk", ascending=False)

# color-code risk
def risk_color(val):
    if val == 0: return 'color:#00FF9D;font-weight:bold'
    elif val <= 2: return 'color:#FFB300;font-weight:bold'
    else: return 'color:#FF4C4C;font-weight:bold'

st.dataframe(risk_table.style.applymap(risk_color, subset=['High_Risk','Issues']), use_container_width=True)

# ================== DETAILED FINDINGS ==================
st.subheader("📄 Detailed Scan Results")
def badge(sev):
    if sev=="Low": return "🟢 LOW"
    if sev=="Medium": return "🟡 MEDIUM"
    return "🔴 HIGH"

df_view = df.copy()
df_view["severity"] = df_view["severity"].apply(badge)
st.dataframe(df_view, use_container_width=True)

st.markdown("---")
st.caption("🛠️ DAST Dashboard | SOC-style Dark Mode | Professional Presentation")
