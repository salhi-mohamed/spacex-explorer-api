import streamlit as st
import json
import pandas as pd
import logging
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# Logging Setup
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("security_dashboard")

# =====================================================
# Safe JSON Loader
# =====================================================
def load_json_file(filepath):
    if not os.path.exists(filepath):
        logger.info(f"[SKIP] File not found: {filepath}")
        return None

    if os.path.getsize(filepath) == 0:
        logger.info(f"[SKIP] Empty file: {filepath}")
        return None

    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        logger.info(f"[OK] Loaded {filepath}")
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"[SKIP] Invalid JSON in {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error reading {filepath}: {e}")
        return None

# =====================================================
# Load SAST Results
# =====================================================
bandit_data = load_json_file("bandit-report.json")
bandit_results = (
    pd.DataFrame(bandit_data.get("results", []))
    if bandit_data else pd.DataFrame()
)

if not bandit_results.empty:
    bandit_results["endpoint"] = bandit_results["filename"]

safety_data = load_json_file("safety-report.json")
safety_results = (
    pd.DataFrame(safety_data.get("vulnerabilities", []))
    if safety_data else pd.DataFrame()
)

if not safety_results.empty:
    safety_results["package"] = safety_results["package_name"]

# =====================================================
# Page Configuration
# =====================================================
st.set_page_config(
    page_title="Enterprise SAST Security Dashboard",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# Professional Dark Mode Styling
# =====================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
    }
    
    h1 {
        color: #00d9ff;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
    }
    
    h2, h3 {
        color: #7dd3fc;
        font-weight: 600;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    .severity-critical {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .severity-high {
        background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .severity-medium {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .severity-low {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .info-box {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .success-box {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    .scan-timestamp {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# Sidebar - Filters & Info
# =====================================================
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1a1f3a/00d9ff?text=SecOps", use_container_width=True)
    st.markdown("### 🔍 Dashboard Filters")
    
    # Severity filter for Bandit
    if not bandit_results.empty:
        severity_options = ["All"] + sorted(bandit_results["issue_severity"].unique().tolist())
        selected_severity = st.multiselect(
            "Filter by Severity",
            options=severity_options,
            default=["All"]
        )
    
    st.markdown("---")
    st.markdown("### 📊 Scan Information")
    st.markdown(f"""
    <div class='info-box'>
        <strong>Scan Date:</strong><br/>
        {datetime.now().strftime("%B %d, %Y %H:%M")}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🛡️ Security Standards")
    st.markdown("""
    - OWASP Top 10
    - CWE/SANS Top 25
    - PCI DSS Compliance
    - NIST Framework
    """)

# =====================================================
# Header Section
# =====================================================
st.markdown("<h1>🔒 Enterprise Security Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("""
<p style='color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem;'>
Comprehensive Static Application Security Testing (SAST) & Software Composition Analysis (SCA) Report
</p>
""", unsafe_allow_html=True)

# =====================================================
# Executive Summary KPIs
# =====================================================
st.markdown("## 📈 Executive Summary")

col1, col2, col3, col4 = st.columns(4)

total_issues = len(bandit_results) + len(safety_results)
critical_issues = len(bandit_results[bandit_results["issue_severity"].str.lower() == "high"]) if not bandit_results.empty else 0

with col1:
    st.metric(
        label="Total Security Issues",
        value=total_issues,
        delta=f"{critical_issues} Critical" if critical_issues > 0 else "No Critical",
        delta_color="inverse"
    )

with col2:
    st.metric(
        label="SAST Findings (Bandit)",
        value=len(bandit_results),
        help="Code-level security vulnerabilities detected"
    )

with col3:
    st.metric(
        label="Vulnerable Dependencies",
        value=len(safety_results),
        help="Third-party packages with known CVEs"
    )

with col4:
    risk_score = min(100, (len(bandit_results) * 5) + (len(safety_results) * 3))
    st.metric(
        label="Risk Score",
        value=f"{risk_score}/100",
        delta="High Risk" if risk_score > 70 else "Moderate",
        delta_color="inverse" if risk_score > 70 else "off"
    )

st.markdown("---")

# =====================================================
# Severity Distribution Charts
# =====================================================
if not bandit_results.empty:
    st.markdown("## 🎯 Vulnerability Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Severity Distribution")
        severity_counts = bandit_results["issue_severity"].value_counts().reset_index()
        severity_counts.columns = ["Severity", "Count"]
        
        color_map = {
            "HIGH": "#dc2626",
            "MEDIUM": "#f59e0b",
            "LOW": "#10b981"
        }
        
        fig = px.pie(
            severity_counts,
            values="Count",
            names="Severity",
            color="Severity",
            color_discrete_map=color_map,
            hole=0.4
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ffffff", size=14),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Confidence Level Distribution")
        confidence_counts = bandit_results["issue_confidence"].value_counts().reset_index()
        confidence_counts.columns = ["Confidence", "Count"]
        
        fig = px.bar(
            confidence_counts,
            x="Confidence",
            y="Count",
            color="Count",
            color_continuous_scale="Turbo"
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ffffff", size=14),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =====================================================
# Bandit SAST Results
# =====================================================
st.markdown("## 🛠️ Static Application Security Testing (SAST) - Bandit")

if not bandit_results.empty:
    
    # Apply severity filter
    filtered_bandit = bandit_results.copy()
    if 'selected_severity' in locals() and "All" not in selected_severity:
        filtered_bandit = bandit_results[bandit_results["issue_severity"].isin(selected_severity)]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h3 style='margin: 0; font-size: 0.9rem; color: #94a3b8;'>TOTAL FINDINGS</h3>
            <p style='font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0; color: #00d9ff;'>{}</p>
        </div>
        """.format(len(filtered_bandit)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <h3 style='margin: 0; font-size: 0.9rem; color: #94a3b8;'>AFFECTED FILES</h3>
            <p style='font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0; color: #7dd3fc;'>{}</p>
        </div>
        """.format(filtered_bandit["endpoint"].nunique()), unsafe_allow_html=True)
    
    with col3:
        high_severity = len(filtered_bandit[filtered_bandit["issue_severity"].str.lower() == "high"])
        st.markdown("""
        <div class='metric-card'>
            <h3 style='margin: 0; font-size: 0.9rem; color: #94a3b8;'>HIGH SEVERITY</h3>
            <p style='font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0; color: #dc2626;'>{}</p>
        </div>
        """.format(high_severity), unsafe_allow_html=True)
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Top vulnerable files
    st.markdown("### 🔥 Most Vulnerable Files")
    top_files = (
        filtered_bandit.groupby("endpoint")
        .agg({
            "issue_severity": lambda x: (x.str.lower() == "high").sum(),
            "endpoint": "count"
        })
        .rename(columns={"issue_severity": "High Severity", "endpoint": "Total Issues"})
        .sort_values("High Severity", ascending=False)
        .head(10)
        .reset_index()
    )
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_files["endpoint"],
        x=top_files["High Severity"],
        name="High Severity",
        orientation='h',
        marker=dict(color='#dc2626')
    ))
    fig.add_trace(go.Bar(
        y=top_files["endpoint"],
        x=top_files["Total Issues"] - top_files["High Severity"],
        name="Other",
        orientation='h',
        marker=dict(color='#f59e0b')
    ))
    fig.update_layout(
        barmode='stack',
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff", size=12),
        xaxis_title="Number of Issues",
        yaxis_title="File Path",
        height=400,
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed findings table
    st.markdown("### 📋 Detailed Security Findings")
    
    def format_severity(sev):
        sev_lower = sev.lower()
        if sev_lower == "high":
            return "🔴 HIGH"
        elif sev_lower == "medium":
            return "🟡 MEDIUM"
        else:
            return "🟢 LOW"
    
    def format_confidence(conf):
        conf_lower = conf.lower()
        if conf_lower == "high":
            return "⚡ High"
        elif conf_lower == "medium":
            return "⚠️ Medium"
        else:
            return "ℹ️ Low"
    
    display_df = filtered_bandit[
        ["filename", "line_number", "issue_severity", "issue_confidence", "issue_text"]
    ].copy()
    
    display_df["issue_severity"] = display_df["issue_severity"].apply(format_severity)
    display_df["issue_confidence"] = display_df["issue_confidence"].apply(format_confidence)
    display_df.columns = ["File", "Line", "Severity", "Confidence", "Description"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )
    
else:
    st.markdown("""
    <div class='success-box'>
        <strong>✅ No SAST vulnerabilities detected</strong><br/>
        Your codebase passed static analysis without any security issues.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =====================================================
# Safety SCA Results
# =====================================================
st.markdown("## 📦 Software Composition Analysis (SCA) - Safety")

if not safety_results.empty:
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h3 style='margin: 0; font-size: 0.9rem; color: #94a3b8;'>TOTAL CVEs</h3>
            <p style='font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0; color: #f59e0b;'>{}</p>
        </div>
        """.format(len(safety_results)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <h3 style='margin: 0; font-size: 0.9rem; color: #94a3b8;'>VULNERABLE PACKAGES</h3>
            <p style='font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0; color: #fbbf24;'>{}</p>
        </div>
        """.format(safety_results["package"].nunique()), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <h3 style='margin: 0; font-size: 0.9rem; color: #94a3b8;'>REMEDIATION PRIORITY</h3>
            <p style='font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0; color: #dc2626;'>HIGH</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Most vulnerable packages
    st.markdown("### ⚠️ High-Risk Dependencies")
    
    vuln_by_package = (
        safety_results.groupby("package")
        .size()
        .reset_index(name="CVE Count")
        .sort_values("CVE Count", ascending=False)
        .head(10)
    )
    
    fig = px.bar(
        vuln_by_package,
        x="CVE Count",
        y="package",
        orientation='h',
        color="CVE Count",
        color_continuous_scale=["#10b981", "#f59e0b", "#dc2626"]
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff", size=12),
        xaxis_title="Number of CVEs",
        yaxis_title="Package Name",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed vulnerability table
    st.markdown("### 📋 Vulnerability Details")
    
    display_safety = safety_results[
        ["package", "affected_versions", "advisory", "id"]
    ].copy()
    display_safety.columns = ["Package", "Affected Versions", "Advisory", "CVE ID"]
    
    st.dataframe(
        display_safety,
        use_container_width=True,
        height=400
    )
    
    # Remediation guidance
    st.markdown("""
    <div class='warning-box'>
        <strong>🔧 Remediation Recommendations</strong><br/>
        1. Update vulnerable packages to their latest secure versions<br/>
        2. Review and apply security patches immediately<br/>
        3. Consider alternative packages if updates are unavailable<br/>
        4. Implement dependency scanning in your CI/CD pipeline
    </div>
    """, unsafe_allow_html=True)
    
else:
    st.markdown("""
    <div class='success-box'>
        <strong>✅ No vulnerable dependencies detected</strong><br/>
        All third-party packages are up-to-date and free of known CVEs.
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# Recommendations & Next Steps
# =====================================================
st.markdown("---")
st.markdown("## 🎯 Security Recommendations")

if total_issues > 0:
    recommendations = f"""
    <div class='info-box'>
        <strong>Priority Actions:</strong><br/><br/>
        
        <strong>1. Immediate (Critical/High Priority):</strong><br/>
        • Address {critical_issues} high-severity code vulnerabilities<br/>
        • Update {len(safety_results)} vulnerable dependencies to secure versions<br/>
        • Review and remediate authentication/authorization issues<br/><br/>
        
        <strong>2. Short-term (This Sprint):</strong><br/>
        • Refactor code with medium-severity findings<br/>
        • Implement input validation and sanitization<br/>
        • Enable automated security scanning in CI/CD pipeline<br/><br/>
        
        <strong>3. Long-term (Continuous Improvement):</strong><br/>
        • Establish security code review process<br/>
        • Conduct security training for development team<br/>
        • Implement runtime application self-protection (RASP)<br/>
        • Schedule regular penetration testing
    </div>
    """
    st.markdown(recommendations, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class='success-box'>
        <strong>🎉 Excellent Security Posture!</strong><br/>
        Your application demonstrates strong security practices. Continue monitoring and maintain regular security scans.
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# Footer
# =====================================================
st.markdown("---")
st.markdown("""
<center style='color: #64748b; padding: 2rem 0;'>
    <strong>Enterprise Security Dashboard</strong> • Powered by Bandit & Safety<br/>
    <small>Last Updated: {}</small>
</center>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)