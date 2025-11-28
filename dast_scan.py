# dast_scan.py
import requests

BASE_URL = "http://127.0.0.1:8000"
endpoints = [
    "/info",
    "/launches/upcoming",
    "/launches/past",
    "/launches/latest",
    "/rockets"
]

# payloads simples pour test d'injection
payloads = ["", "' OR '1'='1", "<script>alert(1)</script>"]

for endpoint in endpoints:
    url = f"{BASE_URL}{endpoint}"
    for payload in payloads:
        try:
            r = requests.get(url, params={"test": payload}, timeout=5)
            print(f"[{r.status_code}] {url}?test={payload}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {url} - {e}")
