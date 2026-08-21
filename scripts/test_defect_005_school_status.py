import urllib.request
import json


BASE_URL = "http://127.0.0.1:8000"

def test_status_update():
    # Login as Super Admin to get token
    url = f"{BASE_URL}/api/v1/auth/login"
    data = json.dumps({"school_code": "VGS001", "email": "superadmin@schoolos.com", "password": "SuperAdmin123!"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode('utf-8'))
        token = res_json.get("access_token")

    # Get school ID
    req_sch = urllib.request.Request(f"{BASE_URL}/api/v1/schools", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req_sch) as resp_sch:
        res = json.loads(resp_sch.read().decode('utf-8'))
        schools_data = res.get("data", res)
        items = schools_data.get("items") if isinstance(schools_data, dict) else schools_data
        school_id = items[0]["id"]
        print(f"Testing school status update on School ID: {school_id}")

    # Send status update PUT
    status_payload = json.dumps({"status": "SUSPENDED", "suspension_reason": "Audit Test"}).encode('utf-8')
    req_put = urllib.request.Request(
        f"{BASE_URL}/api/v1/schools/{school_id}/status",
        data=status_payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req_put) as resp_put:
            print(f"PUT Status Response: {resp_put.status}, Data: {resp_put.read().decode('utf-8')}")
    except Exception as e:
        print(f"PUT Status Error: {e}")

if __name__ == "__main__":
    test_status_update()
