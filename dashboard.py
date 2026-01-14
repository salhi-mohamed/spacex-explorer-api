import streamlit as st
import json
import pandas as pd
import logging
import os

# ---- Setup Logging ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("security_dashboard")

# ---- Helper function to safely load JSON ----
def load_json_file(filepath):
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        st.error(f"File not found: {filepath}")
        return None
    if os.path.getsize(filepath) == 0:
        logger.error(f"File is empty: {filepath}")
        st.error(f"File is empty: {filepath}")
        return None
    try:
        with open(filepath) as f:
            data = json.load(f)
        logger.info(f"Successfully loaded {filepath}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {filepath}: {e}")
        st.error(f"JSON decode error in {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {filepath}: {e}")
        st.error(f"Unexpected error reading {filepath}: {e}")
        return None

# ---- Load Bandit SAST Results ----
bandit_data = load_json_file("bandit-report.json")
bandit_results = pd.DataFrame(bandit_data["results"]) if bandit_data and "results" in bandit_data else pd.DataFrame()
if not bandit_results.empty:
    bandit_results["endpoint"] = bandit_results["filename"]  # use filename as endpoint proxy

# ---- Load Safety Dependency Scan Results ----
safety_data = load_json_file("safety-report.json")
safety_results = pd.DataFrame(safety_data["vulnerabilities"]) if safety_data and "vulnerabilities" in safety_data else pd.DataFrame()
if not safety_results.empty:
    safety_results["package"] = safety_results["package_name"]

# ---- Streamlit Layout ----
st.set_page_config(page_title="SAST Security Dashboard", layout="wide")

# ---- Dark Mode CSS & Styling ----
st.markdown("""
<style>
body { background-color: #0E1117; color: #FAFAFA; }
.stApp { background-color: #0E1117; }
h1, h2, h3, h4, h5 { color: #00FF9D; }
table, th, td { color: #FAFAFA !important; }
.badge-low { background-color:#00FF9D; color:#000; padding:3px 8px; border-radius:5px; font-weight:bold; }
.badge-medium { background-color:#FFB300; color:#000; padding:3px 8px; border-radius:5px; font-weight:bold; }
.badge-high { background-color:#FF4C4C; color:#fff; padding:3px 8px; border-radius:5px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

st.title("🔒 DevSecOps SAST Security Dashboard")
st.markdown("> Professional dark-mode dashboard for static analysis (Bandit) & dependency scans (Safety)")

# ---- Summary Indicators ----
col1, col2, col3 = st.columns(3)
col1.metric("🛠 SAST Issues (Bandit)", len(bandit_results))
col2.metric("📦 Vulnerable Packages (Safety)", len(safety_results))
col3.metric("📌 Endpoints Affected", bandit_results["endpoint"].nunique() if not bandit_results.empty else 0)

st.markdown("---")

# ---- Bandit Issues ----
st.subheader("🛠 Bandit SAST Issues by Endpoint/File")
if not bandit_results.empty:
    # Summary metrics
    total_issues = len(bandit_results)
    unique_endpoints = bandit_results["endpoint"].nunique()
    col1, col2 = st.columns(2)
    col1.metric("Total SAST Issues", total_issues)
    col2.metric("Unique Endpoints Affected", unique_endpoints)

    # Top endpoints with most issues
    st.markdown("### Top Endpoints with Most Issues")
    top_endpoints = (
        bandit_results.groupby("endpoint")
        .size()
        .reset_index(name="Issues Count")
        .sort_values(by="Issues Count", ascending=False)
        .head(10)
    )
    st.table(top_endpoints.style.set_properties(**{'background-color': '#161B22', 'color':'#00FF9D'}))

    # Detailed Bandit table with severity badges
    st.markdown("### Detailed Bandit Results")
    bandit_display = bandit_results[["filename", "line_number", "issue_severity", "issue_confidence", "issue_text"]].copy()
    def severity_badge(sev):
        if sev.lower() == "low": return "🟢 LOW"
        if sev.lower() == "medium": return "🟡 MEDIUM"
        return "🔴 HIGH"
    bandit_display["issue_severity"] = bandit_display["issue_severity"].apply(severity_badge)
    st.dataframe(bandit_display)
else:
    st.info("No SAST issues found!")

st.markdown("---")

# ---- Safety Vulnerable Packages ----
st.subheader("📦 Vulnerable Dependencies (Safety)")
if not safety_results.empty:
    # Summary metrics
    total_vulnerable = len(safety_results)
    unique_packages = safety_results["package"].nunique()
    col1, col2 = st.columns(2)
    col1.metric("Total Vulnerabilities", total_vulnerable)
    col2.metric("Unique Vulnerable Packages", unique_packages)

    # Top vulnerable packages
    st.markdown("### Top Vulnerable Packages")
    top_packages = (
        safety_results.groupby("package")
        .size()
        .reset_index(name="Vulnerability Count")
        .sort_values(by="Vulnerability Count", ascending=False)
        .head(10)
    )
    st.table(top_packages.style.set_properties(**{'background-color': '#161B22', 'color':'#FFB300'}))

    # Detailed table
    st.markdown("### Detailed Vulnerable Dependencies")
    safety_display = safety_results[["package", "affected_versions", "advisory", "id"]].copy()
    st.dataframe(safety_display.style.set_properties(**{'background-color': '#161B22', 'color':'#FAFAFA'}))
else:
    st.info("No vulnerable dependencies found.")
