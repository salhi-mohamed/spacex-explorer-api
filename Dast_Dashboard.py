import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
.metric-card {
    background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
    border-radius: 10px;
    padding: 20px;
    border-left: 4px solid #00FF9D;
}
.vulnerability-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
}
.badge-critical { background-color: #FF4C4C; color: white; }
.badge-high { background-color: #FF6B35; color: white; }
.badge-medium { background-color: #FFB300; color: black; }
.badge-low { background-color: #00FF9D; color: black; }
.badge-info { background-color: #4A9EFF; color: white; }
</style>
""", unsafe_allow_html=True)

# ================== LOAD DATA ==================
try:
    with open("dast_results.json") as f:
        data = json.load(f)
        df = pd.DataFrame(data)
    
    # Get scan metadata
    if len(df) > 0:
        scan_id = df['scan_id'].iloc[0]
        scan_time = df['timestamp'].iloc[0]
    else:
        scan_id = "N/A"
        scan_time = "N/A"
        
except FileNotFoundError:
    st.error("❌ DAST results file not found. Please run the scan first.")
    st.stop()

# ================== HEADER ==================
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.title("🛡️ DAST Security Dashboard")
    st.caption("SpaceX Explorer API - Dynamic Application Security Testing")
with col2:
    st.metric("Scan ID", scan_id)
with col3:
    st.metric("Scan Time", scan_time)

st.markdown("---")

# ================== EXECUTIVE SUMMARY ==================
st.subheader("📊 Executive Summary")

# Calculate metrics
total_requests = len(df)
issues_df = df[df["findings"].apply(lambda x: len(x) > 0)]
total_findings = df["findings"].apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
high_risk_count = len(df[df["severity"] == "High"])
medium_risk_count = len(df[df["severity"] == "Medium"])
low_risk_count = len(df[df["severity"] == "Low"])
unique_endpoints = df["endpoint"].nunique()
avg_response_time = df["duration_sec"].mean()

# KPI Cards
kpi_cols = st.columns(6)
kpi_cols[0].metric("🔍 Total Tests", total_requests)
kpi_cols[1].metric("⚠️ Total Findings", total_findings)
kpi_cols[2].metric("🔴 High Severity", high_risk_count, delta=f"{high_risk_count} critical" if high_risk_count > 0 else None, delta_color="inverse")
kpi_cols[3].metric("🟡 Medium Severity", medium_risk_count)
kpi_cols[4].metric("🟢 Low Severity", low_risk_count)
kpi_cols[5].metric("⚡ Avg Response", f"{avg_response_time:.2f}s")

st.markdown("---")

# ================== SECURITY POSTURE ==================
st.subheader("🎯 Security Posture Overview")

col1, col2 = st.columns(2)

with col1:
    # Severity Distribution Pie Chart
    severity_counts = df["severity"].value_counts()
    fig_severity = px.pie(
        values=severity_counts.values,
        names=severity_counts.index,
        title="Severity Distribution",
        template="plotly_dark",
        color=severity_counts.index,
        color_discrete_map={
            "High": "#FF4C4C",
            "Medium": "#FFB300",
            "Low": "#00FF9D"
        },
        hole=0.4
    )
    fig_severity.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_severity, use_container_width=True)

with col2:
    # Attack Type Coverage
    attack_counts = df["attack_type"].value_counts().reset_index()
    attack_counts.columns = ["Attack Type", "Count"]
    
    fig_attack = px.bar(
        attack_counts,
        x="Attack Type",
        y="Count",
        title="Attack Vector Coverage",
        template="plotly_dark",
        color="Count",
        color_continuous_scale=["#00FF9D", "#FFB300", "#FF4C4C"],
        text="Count"
    )
    fig_attack.update_traces(textposition='outside')
    fig_attack.update_layout(showlegend=False)
    st.plotly_chart(fig_attack, use_container_width=True)

st.markdown("---")

# ================== ENDPOINT ANALYSIS ==================
st.subheader("🌐 Endpoint Security Analysis")

# Endpoint risk aggregation
endpoint_analysis = df.groupby("endpoint").agg(
    Total_Tests=("endpoint", "count"),
    Total_Findings=("findings", lambda x: sum(len(f) if isinstance(f, list) else 0 for f in x)),
    High_Severity=("severity", lambda x: (x == "High").sum()),
    Medium_Severity=("severity", lambda x: (x == "Medium").sum()),
    Low_Severity=("severity", lambda x: (x == "Low").sum()),
    Avg_Response_Time=("duration_sec", "mean")
).reset_index()

# Calculate risk score (weighted)
endpoint_analysis["Risk_Score"] = (
    endpoint_analysis["High_Severity"] * 10 +
    endpoint_analysis["Medium_Severity"] * 5 +
    endpoint_analysis["Low_Severity"] * 1
)
endpoint_analysis = endpoint_analysis.sort_values("Risk_Score", ascending=False)

# Risk Score Bar Chart
fig_endpoint = px.bar(
    endpoint_analysis,
    x="endpoint",
    y="Risk_Score",
    title="Endpoint Risk Scores (Weighted)",
    template="plotly_dark",
    color="Risk_Score",
    color_continuous_scale=["#00FF9D", "#FFB300", "#FF4C4C"],
    text="Risk_Score"
)
fig_endpoint.update_traces(textposition='outside')
fig_endpoint.update_xaxes(tickangle=-45)
st.plotly_chart(fig_endpoint, use_container_width=True)

# Endpoint table with styling
def highlight_risk(row):
    if row['Risk_Score'] >= 20:
        return ['background-color: #FF4C4C; color: white'] * len(row)
    elif row['Risk_Score'] >= 10:
        return ['background-color: #FFB300; color: black'] * len(row)
    else:
        return ['background-color: #00FF9D; color: black'] * len(row)

st.dataframe(
    endpoint_analysis.style.format({
        "Avg_Response_Time": "{:.2f}s",
        "Risk_Score": "{:.0f}"
    }),
    use_container_width=True
)

st.markdown("---")

# ================== VULNERABILITY BREAKDOWN ==================
st.subheader("🔍 Vulnerability Details by Attack Type")

# Expand findings to get vulnerability breakdown
findings_list = []
for _, row in df.iterrows():
    if isinstance(row['findings'], list) and len(row['findings']) > 0:
        for finding in row['findings']:
            findings_list.append({
                'endpoint': row['endpoint'],
                'attack_type': row['attack_type'],
                'severity': row['severity'],
                'finding': finding,
                'status_code': row['status_code']
            })

if findings_list:
    findings_df = pd.DataFrame(findings_list)
    
    # Vulnerability count by attack type
    vuln_by_attack = findings_df.groupby(['attack_type', 'severity']).size().reset_index(name='count')
    
    fig_vuln = px.bar(
        vuln_by_attack,
        x='attack_type',
        y='count',
        color='severity',
        title='Vulnerabilities by Attack Type',
        template='plotly_dark',
        color_discrete_map={
            "High": "#FF4C4C",
            "Medium": "#FFB300",
            "Low": "#00FF9D"
        },
        text='count',
        barmode='group'
    )
    fig_vuln.update_traces(textposition='outside')
    st.plotly_chart(fig_vuln, use_container_width=True)
    
    # Detailed findings table
    st.markdown("#### 📋 All Detected Issues")
    
    # Add badge column
    def severity_badge(sev):
        if sev == "High":
            return "🔴 HIGH"
        elif sev == "Medium":
            return "🟡 MEDIUM"
        else:
            return "🟢 LOW"
    
    findings_df['severity_badge'] = findings_df['severity'].apply(severity_badge)
    
    # Display with filters
    attack_filter = st.multiselect(
        "Filter by Attack Type:",
        options=findings_df['attack_type'].unique(),
        default=findings_df['attack_type'].unique()
    )
    
    filtered_findings = findings_df[findings_df['attack_type'].isin(attack_filter)]
    
    st.dataframe(
        filtered_findings[['endpoint', 'attack_type', 'severity_badge', 'finding', 'status_code']].rename(
            columns={
                'endpoint': 'Endpoint',
                'attack_type': 'Attack Type',
                'severity_badge': 'Severity',
                'finding': 'Finding',
                'status_code': 'HTTP Status'
            }
        ),
        use_container_width=True,
        height=400
    )
else:
    st.success("✅ No vulnerabilities detected! Application appears secure against tested attack vectors.")

st.markdown("---")

# ================== RESPONSE TIME ANALYSIS ==================
st.subheader("⏱️ Performance & Response Time Analysis")

col1, col2 = st.columns(2)

with col1:
    # Response time by endpoint
    resp_time_by_endpoint = df.groupby('endpoint')['duration_sec'].mean().reset_index()
    resp_time_by_endpoint.columns = ['Endpoint', 'Avg Response Time (s)']
    
    fig_resp = px.bar(
        resp_time_by_endpoint,
        x='Endpoint',
        y='Avg Response Time (s)',
        title='Average Response Time by Endpoint',
        template='plotly_dark',
        color='Avg Response Time (s)',
        color_continuous_scale='Viridis',
        text='Avg Response Time (s)'
    )
    fig_resp.update_traces(texttemplate='%{text:.2f}s', textposition='outside')
    fig_resp.update_xaxes(tickangle=-45)
    st.plotly_chart(fig_resp, use_container_width=True)

with col2:
    # Response time distribution
    fig_dist = px.histogram(
        df,
        x='duration_sec',
        nbins=20,
        title='Response Time Distribution',
        template='plotly_dark',
        color_discrete_sequence=['#00FF9D']
    )
    fig_dist.update_xaxes(title='Response Time (seconds)')
    fig_dist.update_yaxes(title='Frequency')
    st.plotly_chart(fig_dist, use_container_width=True)

st.markdown("---")

# ================== HTTP STATUS ANALYSIS ==================
st.subheader("📡 HTTP Status Code Analysis")

status_counts = df['status_code'].astype(str).value_counts().reset_index()
status_counts.columns = ['Status Code', 'Count']

fig_status = px.bar(
    status_counts,
    x='Status Code',
    y='Count',
    title='HTTP Status Code Distribution',
    template='plotly_dark',
    color='Status Code',
    color_discrete_map={
        "200": "#00FF9D",
        "400": "#FFB300",
        "401": "#FF6B35",
        "403": "#FF4C4C",
        "404": "#FF6B6B",
        "500": "#FF0000",
        "TIMEOUT": "#8B0000",
        "ERROR": "#8B0000"
    },
    text='Count'
)
fig_status.update_traces(textposition='outside')
st.plotly_chart(fig_status, use_container_width=True)

st.markdown("---")

# ================== DETAILED SCAN RESULTS ==================
st.subheader("📄 Complete Scan Results")

# Prepare display dataframe
df_display = df.copy()

# Format findings
df_display["findings_display"] = df_display["findings"].apply(
    lambda x: "\n".join([f"• {item}" for item in x]) if isinstance(x, list) and len(x) > 0 else "✅ No issues"
)

# Format severity with emojis
def format_severity(sev):
    if sev == "High":
        return "🔴 HIGH"
    elif sev == "Medium":
        return "🟡 MEDIUM"
    else:
        return "🟢 LOW"

df_display["severity_display"] = df_display["severity"].apply(format_severity)

# Select columns to display
display_cols = [
    'endpoint', 'attack_type', 'payload', 'status_code', 
    'response_length', 'duration_sec', 'severity_display', 'findings_display'
]

df_final = df_display[display_cols].rename(columns={
    'endpoint': 'Endpoint',
    'attack_type': 'Attack Type',
    'payload': 'Payload',
    'status_code': 'HTTP Status',
    'response_length': 'Response Size (bytes)',
    'duration_sec': 'Response Time (s)',
    'severity_display': 'Severity',
    'findings_display': 'Findings'
})

# Add filters
col1, col2, col3 = st.columns(3)
with col1:
    endpoint_filter = st.multiselect(
        "Filter by Endpoint:",
        options=df['endpoint'].unique(),
        default=df['endpoint'].unique()
    )
with col2:
    severity_filter = st.multiselect(
        "Filter by Severity:",
        options=['High', 'Medium', 'Low'],
        default=['High', 'Medium', 'Low']
    )
with col3:
    attack_filter_detailed = st.multiselect(
        "Filter by Attack:",
        options=df['attack_type'].unique(),
        default=df['attack_type'].unique()
    )

# Apply filters
filtered_df = df_display[
    (df_display['endpoint'].isin(endpoint_filter)) &
    (df_display['severity'].isin(severity_filter)) &
    (df_display['attack_type'].isin(attack_filter_detailed))
]

df_filtered_display = filtered_df[display_cols].rename(columns={
    'endpoint': 'Endpoint',
    'attack_type': 'Attack Type',
    'payload': 'Payload',
    'status_code': 'HTTP Status',
    'response_length': 'Response Size (bytes)',
    'duration_sec': 'Response Time (s)',
    'severity_display': 'Severity',
    'findings_display': 'Findings'
})

st.dataframe(df_filtered_display, use_container_width=True, height=500)

# Download button
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Full Report (CSV)",
    data=csv,
    file_name=f"dast_report_{scan_id}.csv",
    mime="text/csv"
)

st.markdown("---")

# ================== RECOMMENDATIONS ==================
st.subheader("💡 Security Recommendations")

if high_risk_count > 0:
    st.error(f"🔴 **CRITICAL**: {high_risk_count} high-severity issues detected. Immediate action required!")
    st.markdown("""
    **Immediate Actions:**
    - Review all High severity findings above
    - Implement input validation and sanitization
    - Apply security patches and updates
    - Consider taking affected endpoints offline until fixed
    """)

if medium_risk_count > 0:
    st.warning(f"🟡 **WARNING**: {medium_risk_count} medium-severity issues found. Address soon.")
    st.markdown("""
    **Recommended Actions:**
    - Implement security headers (CSP, X-XSS-Protection, etc.)
    - Review and update input validation logic
    - Schedule security fixes in next sprint
    """)

if high_risk_count == 0 and medium_risk_count == 0:
    st.success("✅ **GOOD**: No critical vulnerabilities detected!")
    st.markdown("""
    **Maintenance Recommendations:**
    - Continue regular security scans
    - Keep dependencies updated
    - Monitor for new vulnerability disclosures
    - Maintain security headers and best practices
    """)

st.markdown("---")
st.caption("🛠️ DAST Security Dashboard | Powered by Streamlit | Professional Security Assessment")