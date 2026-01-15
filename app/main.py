from fastapi import FastAPI, HTTPException, Request, Response
import requests, time, uuid, json, logging
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="SpaceX Explorer API")
BASE_V5 = "https://api.spacexdata.com/v5"
BASE_V4 = "https://api.spacexdata.com/v4"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("spacex_api")

REQUEST_COUNTER = Counter("spacex_requests_total", "Total number of requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("spacex_request_latency_seconds", "Request latency in seconds", ["method", "path"])
ERROR_COUNTER = Counter("spacex_errors_total", "Total number of failed requests", ["method", "path", "status"])

# ---------------------- tracing + logging middleware ----------------------
@app.middleware("http")
async def log_and_trace(request: Request, call_next):
    # trace id: reuse header if present else create one
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    request.state.trace_id = trace_id

    start = time.time()
    method = request.method
    path = request.url.path

    logger.info(json.dumps({
        "ts": int(start*1000), "event":"request_received",
        "trace_id": trace_id, "method": method, "path": path
    }))

    try:
        response = await call_next(request)
        status = response.status_code
    except Exception as exc:
        now = time.time()
        duration_s = now - start
        try:
            REQUEST_COUNTER.labels(method=method, path=path, status="500").inc()
            REQUEST_LATENCY.labels(method=method, path=path).observe(duration_s)
            ERROR_COUNTER.labels(method=method, path=path, status="500").inc()
        except Exception:
            pass
        logger.error(json.dumps({
            "ts": int(now*1000), "event":"exception",
            "trace_id": trace_id, "method": method, "path": path, "error": str(exc)
        }))
        raise

    end = time.time()
    duration_s = end - start
    duration_ms = int(duration_s * 1000)

    try:
        REQUEST_COUNTER.labels(method=method, path=path, status=str(status)).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(duration_s)
        if status >= 400:
            ERROR_COUNTER.labels(method=method, path=path, status=str(status)).inc()
    except Exception:
        pass
    # attach trace id header so clients and downstream can see/correlate it
    response.headers["X-Trace-Id"] = trace_id

    logger.info(json.dumps({
        "ts": int(end*1000), "event":"request_completed",
        "trace_id": trace_id, "method": method, "path": path,
        "status": status, "duration_ms": duration_ms
    }))
    return response
# ---------------------- helper: fetch with trace propagation ----------------------
def fetch_data(url: str, trace_id: str = None):
    headers = {}
    if trace_id:
        headers["X-Trace-Id"] = trace_id
    try:
        t0 = time.time()
        resp = requests.get(url, timeout=10, headers=headers)
        t1 = time.time()
        upstream_ms = int((t1 - t0) * 1000)
        # log upstream timing for trace correlation
        logger.info(json.dumps({
            "ts": int(t1*1000), "event":"upstream_call",
            "trace_id": trace_id, "url": url, "status_code": resp.status_code, "upstream_ms": upstream_ms
        }))
        if resp.status_code != 200:
            raise Exception(f"External API error {resp.status_code}")
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {e}")
# ---------------------- simplifiers ----------------------
def simplify_launch(launch: dict):
    return {
        "name": launch.get("name"), "flight_number": launch.get("flight_number"),
        "date_utc": launch.get("date_utc"), "rocket_id": launch.get("rocket"),
        "success": launch.get("success"), "upcoming": launch.get("upcoming"),
        "details": launch.get("details"), "webcast": launch.get("links", {}).get("webcast"),
        "patch_small": launch.get("links", {}).get("patch", {}).get("small"),
        "patch_large": launch.get("links", {}).get("patch", {}).get("large"),
    }

def simplify_rocket(rocket: dict):
    return {
        "name": rocket.get("name"), "type": rocket.get("type"),
        "first_flight": rocket.get("first_flight"), "country": rocket.get("country"),
        "stages": rocket.get("stages"), "boosters": rocket.get("boosters"),
        "cost_per_launch": rocket.get("cost_per_launch"), "success_rate_pct": rocket.get("success_rate_pct"),
        "height_m": rocket.get("height", {}).get("meters"), "diameter_m": rocket.get("diameter", {}).get("meters"),
        "mass_kg": rocket.get("mass", {}).get("kg"), "description": rocket.get("description"),
    }
# ---------------------- endpoints (pass request to access trace id) ----------------------
@app.get("/launches/upcoming")
def upcoming_launches(request: Request, limit: int = 5):
    launches = fetch_data(f"{BASE_V5}/launches/upcoming", trace_id=request.state.trace_id)
    return [simplify_launch(l) for l in launches[:limit]]
@app.get("/launches/past")
def past_launches(request: Request, limit: int = 5):
    launches = fetch_data(f"{BASE_V5}/launches/past", trace_id=request.state.trace_id)
    return [simplify_launch(l) for l in launches[:limit]]
@app.get("/launches/latest")
def latest_launch(request: Request):
    launch = fetch_data(f"{BASE_V5}/launches/latest", trace_id=request.state.trace_id)
    return simplify_launch(launch)
@app.get("/launches/{launch_id}")
def launch_details(launch_id: str, request: Request):
    launch = fetch_data(f"{BASE_V5}/launches/{launch_id}", trace_id=request.state.trace_id)
    if not launch:
        raise HTTPException(status_code=404, detail="Launch not found")
    return simplify_launch(launch)
@app.get("/rockets")
def rockets(request: Request):
    rockets_data = fetch_data(f"{BASE_V4}/rockets", trace_id=request.state.trace_id)
    return [simplify_rocket(r) for r in rockets_data]
@app.get("/rockets/{rocket_id}")
def rocket_details(rocket_id: str, request: Request):
    rocket = fetch_data(f"{BASE_V4}/rockets/{rocket_id}", trace_id=request.state.trace_id)
    if not rocket:
        raise HTTPException(status_code=404, detail="Rocket not found")
    return simplify_rocket(rocket)
@app.get("/info")
def info(request: Request):
    return {"status": "SpaceX Explorer API is running", "version": "1.0", "trace_id": request.state.trace_id}
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)