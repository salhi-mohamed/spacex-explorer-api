import requests
import json
import time
from datetime import datetime

# -------------------- Logging --------------------
def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}", flush=True)

# -------------------- CONFIG --------------------
log("Starting DAST scan")

BASE_URL = "http://127.0.0.1:60403"
log(f"Using target URL: {BASE_URL}")

endpoints = [
    "/info",
    "/launches/upcoming",
    "/launches/past",
    "/launches/latest",
    "/rockets"
]

payloads = {
    "sql_injection": "' OR '1'='1",
    "xss": "<script>alert(1)</script>",
    "path_traversal": "../../etc/passwd",
    "command_injection": "; ls -la",
    "xxe": "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",
    "normal": "test"
}

results = []
scan_id = int(time.time())
log(f"Scan ID: {scan_id}")
log(f"Total endpoints: {len(endpoints)}")
log(f"Payloads per endpoint: {len(payloads)}")

# -------------------- DETECTION FUNCTIONS --------------------
def detect_sql_injection(response_text, status_code, baseline_length):
    """Enhanced SQL injection detection"""
    findings = []
    
    # SQL error patterns
    sql_errors = [
        "syntax error", "mysql", "postgresql", "sql", "database error",
        "unterminated", "quoted string", "unclosed quotation",
        "you have an error in your sql syntax", "warning: mysql",
        "ora-", "pg_query", "sqlite_", "sqlstate", "mysql_fetch",
        "mysqli", "odbc", "db2_", "ibm db2", "driver error"
    ]
    
    response_lower = response_text.lower()
    for error in sql_errors:
        if error in response_lower:
            findings.append(f"SQL error pattern detected: '{error}'")
            break
    
    # Check for unusual response length (data leakage)
    if baseline_length and abs(len(response_text) - baseline_length) > 100:
        findings.append(f"Response length anomaly: {len(response_text)} vs baseline {baseline_length}")
    
    # Check for status code changes
    if status_code == 500:
        findings.append("Server error 500 - possible SQL injection")
    
    return findings

def detect_xss(payload, response_text, headers):
    """Enhanced XSS detection"""
    findings = []
    
    # Check if payload is reflected without encoding
    if payload in response_text:
        findings.append("XSS payload reflected unencoded in response")
    
    # Check for common XSS patterns
    xss_patterns = ["<script", "javascript:", "onerror=", "onload=", "alert("]
    for pattern in xss_patterns:
        if pattern in response_text.lower():
            findings.append(f"Potential XSS pattern found: '{pattern}'")
    
    # Check Content-Type header
    content_type = headers.get('Content-Type', '').lower()
    if 'text/html' in content_type and payload in response_text:
        findings.append("HTML content type with reflected payload - high XSS risk")
    
    # Check for missing security headers
    if 'X-XSS-Protection' not in headers:
        findings.append("Missing X-XSS-Protection header")
    
    if 'Content-Security-Policy' not in headers:
        findings.append("Missing Content-Security-Policy header")
    
    return findings

def detect_path_traversal(response_text, status_code):
    """Enhanced path traversal detection"""
    findings = []
    
    # Unix/Linux system file patterns
    unix_patterns = [
        "root:", "daemon:", "bin:", "sys:", "/bin/", "/etc/",
        "x:0:0:", "bash", "nologin"
    ]
    
    # Windows system file patterns
    windows_patterns = [
        "[boot loader]", "[operating systems]", "c:\\windows",
        "c:\\winnt", "administrator:"
    ]
    
    response_lower = response_text.lower()
    
    for pattern in unix_patterns:
        if pattern in response_lower:
            findings.append(f"Unix system file pattern detected: '{pattern}'")
            break
    
    for pattern in windows_patterns:
        if pattern in response_lower:
            findings.append(f"Windows system file pattern detected: '{pattern}'")
            break
    
    # Check for directory listing
    if "index of" in response_lower or "directory listing" in response_lower:
        findings.append("Directory listing exposed")
    
    return findings

def detect_command_injection(response_text, status_code):
    """Detect command injection vulnerabilities"""
    findings = []
    
    cmd_patterns = [
        "total ", "drwx", "-rw-", "root root", "bin/bash",
        "uid=", "gid=", "groups="
    ]
    
    for pattern in cmd_patterns:
        if pattern in response_text:
            findings.append(f"Command execution pattern detected: '{pattern}'")
            break
    
    return findings

def detect_security_headers(headers):
    """Check for missing security headers"""
    findings = []
    
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY or SAMEORIGIN',
        'Strict-Transport-Security': 'HSTS',
        'Content-Security-Policy': 'CSP'
    }
    
    for header, description in security_headers.items():
        if header not in headers:
            findings.append(f"Missing security header: {header}")
    
    return findings

# -------------------- BASELINE SCAN --------------------
log("Running baseline scan...")
baseline = {}
for endpoint in endpoints:
    try:
        url = f"{BASE_URL}{endpoint}"
        r = requests.get(url, timeout=5)
        baseline[endpoint] = len(r.text)
        log(f"Baseline for {endpoint}: {len(r.text)} bytes")
    except Exception as e:
        log(f"Baseline failed for {endpoint}: {e}", "WARN")
        baseline[endpoint] = None

# -------------------- SCAN LOOP --------------------
for endpoint in endpoints:
    log(f"Scanning endpoint: {endpoint}")

    for attack, payload in payloads.items():
        url = f"{BASE_URL}{endpoint}"
        log(f"→ Attack={attack} | Payload={payload}")
        log(f"→ URL={url}")

        try:
            start = time.time()
            r = requests.get(url, params={"q": payload}, timeout=5)
            duration = round(time.time() - start, 2)

            # -------------------- DETECTION --------------------
            findings = []
            
            # Attack-specific detection
            if attack == "sql_injection":
                findings.extend(detect_sql_injection(r.text, r.status_code, baseline.get(endpoint)))
            
            elif attack == "xss":
                findings.extend(detect_xss(payload, r.text, r.headers))
            
            elif attack == "path_traversal":
                findings.extend(detect_path_traversal(r.text, r.status_code))
            
            elif attack == "command_injection":
                findings.extend(detect_command_injection(r.text, r.status_code))
            
            # General security checks (only on normal requests)
            if attack == "normal":
                sec_findings = detect_security_headers(r.headers)
                if sec_findings:
                    findings.extend(sec_findings)
            
            # Check for generic payload reflection
            if attack != "normal" and payload in r.text:
                findings.append(f"Payload reflected in response (potential {attack})")
            
            # HTTP error detection
            if r.status_code >= 500:
                findings.append(f"Server error {r.status_code} - possible vulnerability")
            elif r.status_code == 403:
                findings.append("403 Forbidden - possible security control detected")

            # -------------------- SEVERITY --------------------
            if len(findings) > 0:
                # High severity for critical vulnerabilities
                if any(x in str(findings).lower() for x in ["sql", "xss", "command", "path traversal"]):
                    if any(x in str(findings).lower() for x in ["detected", "pattern", "reflected"]):
                        severity = "High"
                    else:
                        severity = "Medium"
                else:
                    severity = "Low"
            else:
                severity = "Low"

            log(
                f"← Status={r.status_code} | Length={len(r.text)} | "
                f"Time={duration}s | Findings={len(findings)} | Severity={severity}"
            )
            
            if findings:
                for finding in findings:
                    log(f"   ⚠ {finding}", "WARN")

            # -------------------- STORE RESULT --------------------
            results.append({
                "scan_id": scan_id,
                "endpoint": endpoint,
                "attack_type": attack,
                "payload": payload,
                "status_code": r.status_code,
                "response_length": len(r.text),
                "duration_sec": duration,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "findings": findings,
                "severity": severity,
                "baseline_length": baseline.get(endpoint)
            })

        except requests.exceptions.Timeout:
            log("Request timed out", "ERROR")
            results.append({
                "scan_id": scan_id,
                "endpoint": endpoint,
                "attack_type": attack,
                "payload": payload,
                "status_code": "TIMEOUT",
                "response_length": 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "findings": ["Request timed out"],
                "severity": "High"
            })

        except Exception as e:
            log(f"Request failed: {e}", "ERROR")
            results.append({
                "scan_id": scan_id,
                "endpoint": endpoint,
                "attack_type": attack,
                "payload": payload,
                "status_code": "ERROR",
                "response_length": 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "findings": [str(e)],
                "severity": "High"
            })

# -------------------- SUMMARY --------------------
log("=" * 60)
log("SCAN SUMMARY")
log("=" * 60)

high_severity = [r for r in results if r.get("severity") == "High"]
medium_severity = [r for r in results if r.get("severity") == "Medium"]
low_severity = [r for r in results if r.get("severity") == "Low"]

log(f"Total tests: {len(results)}")
log(f"High severity findings: {len(high_severity)}")
log(f"Medium severity findings: {len(medium_severity)}")
log(f"Low severity findings: {len(low_severity)}")

if high_severity:
    log("Critical issues found:", "WARN")
    for item in high_severity:
        log(f"  • {item['endpoint']} ({item['attack_type']}): {item['findings']}", "WARN")

# -------------------- SAVE RESULTS --------------------
log("Writing results to dast_results.json")
with open("dast_results.json", "w") as f:
    json.dump(results, f, indent=2)

log("DAST scan completed successfully ✅")