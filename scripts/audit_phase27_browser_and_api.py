"""
Phase 27 Real Product & API Audit Script using Python Standard Library
Executes thorough HTTP requests against live running backend API (http://127.0.0.1:8000)
"""

import json
import urllib.request
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000"

def make_request(path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    headers = headers or {}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    if data is not None and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            body_json = json.loads(content)
        except Exception:
            body_json = {"raw": content}
        return e.code, body_json
    except Exception as e:
        return 0, {"error": str(e)}

def audit():
    print("=== STARTING PHASE 27 REAL PRODUCT & API AUDIT ===")
    defects = []
    
    # 1. Health Endpoints
    print("\n1. Auditing Health & Readiness Probes...")
    status, body = make_request("/health/live")
    if status == 200 and body.get("status") == "alive":
        print("   /health/live: OK (200 alive)")
    else:
        defects.append(("CRITICAL", "Health Probes", f"/health/live returned {status}: {body}"))

    status, body = make_request("/health/ready")
    if status == 200 and body.get("status") == "ready":
        print("   /health/ready: OK (200 ready)")
    else:
        defects.append(("CRITICAL", "Health Probes", f"/health/ready returned {status}: {body}"))

    # 2. CORS Preflight
    print("\n2. Auditing CORS Preflight Headers...")
    status, body = make_request("/api/v1/auth/login", method="OPTIONS", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST"
    })
    print(f"   CORS Options Status: {status}")

    # 3. Authentication Workflows
    print("\n3. Auditing Auth Endpoints (Negative Workflows)...")
    status, body = make_request("/api/v1/auth/login", method="POST", data={})
    if status == 422:
        print("   Empty credentials validation (422): OK")
    else:
        defects.append(("MEDIUM", "Auth", f"Empty login returned {status} instead of 422"))

    status, body = make_request("/api/v1/auth/login", method="POST", data={"email": "fake@user.com", "password": "wrongpassword"})
    if status in (401, 404):
        print(f"   Invalid login rejection ({status}): OK")
    else:
        defects.append(("HIGH", "Auth", f"Invalid login returned {status} instead of 401/404"))

    # 4. OpenAPI Specification
    print("\n4. Auditing OpenAPI Endpoints Schema...")
    status, body = make_request("/openapi.json")
    if status == 200:
        paths = body.get("paths", {})
        print(f"   OpenAPI Spec loaded: {len(paths)} API paths registered.")
    else:
        defects.append(("LOW", "OpenAPI", f"GET /openapi.json returned {status}"))

    print("\n=== PHASE 27 PRELIMINARY API AUDIT COMPLETE ===")
    return defects

if __name__ == "__main__":
    defects = audit()
    if defects:
        print("\nDefects Discovered:")
        for d in defects:
            print(f" - [{d[0]}] {d[1]}: {d[2]}")
