# dast_scan.py
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

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
    "normal": "test"
}

results = []

scan_id = int(time.time())

for endpoint in endpoints:
    for attack, payload in payloads.items():
        url = f"{BASE_URL}{endpoint}"
        try:
            r = requests.get(url, params={"q": payload}, timeout=5)
            results.append({
                "scan_id": scan_id,
                "endpoint": endpoint,
                "attack_type": attack,
                "payload": payload,
                "status_code": r.status_code,
                "response_length": len(r.text),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            results.append({
                "scan_id": scan_id,
                "endpoint": endpoint,
                "attack_type": attack,
                "payload": payload,
                "status_code": "ERROR",
                "response_length": 0,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            })

with open("dast_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("✅ DAST scan completed → dast_results.json generated")
