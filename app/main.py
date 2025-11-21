from fastapi import FastAPI, HTTPException, Request
import requests
import time
import uuid
import json
import logging

app = FastAPI(title="SpaceX Explorer API")


BASE_V5 = "https://api.spacexdata.com/v5"
BASE_V4 = "https://api.spacexdata.com/v4"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("spacex_api")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()
    method = request.method
    path = request.url.path

    # request received
    logger.info(json.dumps({
        "ts": int(start * 1000),
        "event": "request_received",
        "request_id": request_id,
        "method": method,
        "path": path
    }))

    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as exc:
        now = time.time()
        logger.error(json.dumps({
            "ts": int(now * 1000),
            "event": "exception",
            "request_id": request_id,
            "method": method,
            "path": path,
            "error": str(exc)
        }))
        raise

    end = time.time()
    duration_ms = int((end - start) * 1000)
    # request completed
    logger.info(json.dumps({
        "ts": int(end * 1000),
        "event": "request_completed",
        "request_id": request_id,
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": duration_ms
    }))
    return response

def fetch_data(url: str):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            raise Exception(f"External API error {resp.status_code}")
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {e}")

def simplify_launch(launch: dict):
    return {
        "name": launch.get("name"),
        "flight_number": launch.get("flight_number"),
        "date_utc": launch.get("date_utc"),
        "rocket_id": launch.get("rocket"),
        "success": launch.get("success"),
        "upcoming": launch.get("upcoming"),
        "details": launch.get("details"),
        "webcast": launch.get("links", {}).get("webcast"),
        "patch_small": launch.get("links", {}).get("patch", {}).get("small"),
        "patch_large": launch.get("links", {}).get("patch", {}).get("large"),
    }

def simplify_rocket(rocket: dict):
    return {
        "name": rocket.get("name"),
        "type": rocket.get("type"),
        "first_flight": rocket.get("first_flight"),
        "country": rocket.get("country"),
        "stages": rocket.get("stages"),
        "boosters": rocket.get("boosters"),
        "cost_per_launch": rocket.get("cost_per_launch"),
        "success_rate_pct": rocket.get("success_rate_pct"),
        "height_m": rocket.get("height", {}).get("meters"),
        "diameter_m": rocket.get("diameter", {}).get("meters"),
        "mass_kg": rocket.get("mass", {}).get("kg"),
        "description": rocket.get("description"),
    }

@app.get("/launches/upcoming")
def upcoming_launches(limit: int = 5):
    launches = fetch_data(f"{BASE_V5}/launches/upcoming")
    return [simplify_launch(l) for l in launches[:limit]]

@app.get("/launches/past")
def past_launches(limit: int = 5):
    launches = fetch_data(f"{BASE_V5}/launches/past")
    return [simplify_launch(l) for l in launches[:limit]]

@app.get("/launches/latest")
def latest_launch():
    launch = fetch_data(f"{BASE_V5}/launches/latest")
    return simplify_launch(launch)

@app.get("/launches/{launch_id}")
def launch_details(launch_id: str):
    launch = fetch_data(f"{BASE_V5}/launches/{launch_id}")
    if not launch:
        raise HTTPException(status_code=404, detail="Launch not found")
    return simplify_launch(launch)

@app.get("/rockets")
def rockets():
    rockets_data = fetch_data(f"{BASE_V4}/rockets")
    return [simplify_rocket(r) for r in rockets_data]

@app.get("/rockets/{rocket_id}")
def rocket_details(rocket_id: str):
    rocket = fetch_data(f"{BASE_V4}/rockets/{rocket_id}")
    if not rocket:
        raise HTTPException(status_code=404, detail="Rocket not found")
    return simplify_rocket(rocket)

@app.get("/info")
def info():
    """
    Simple endpoint to check the API status
    """
    return {"status": "SpaceX Explorer API is running", "version": "1.0"}
