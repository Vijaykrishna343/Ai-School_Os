import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8000"

def test_login(payload):
    url = f"{BASE_URL}/api/v1/auth/login"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))

print("Test 1: Valid school_code, invalid user email/password")
status1, body1 = test_login({"school_code": "VGS001", "email": "nonexistent@school.com", "password": "wrongpassword"})
print(f"  Status: {status1}, Body: {body1}")

print("Test 2: Valid school_code, valid user, wrong password")
status2, body2 = test_login({"school_code": "VGS001", "email": "principal@vaagdevi.com", "password": "wrongpassword"})
print(f"  Status: {status2}, Body: {body2}")

print("Test 3: Missing required field school_code (Pydantic validation)")
status3, body3 = test_login({"email": "principal@vaagdevi.com", "password": "wrongpassword"})
print(f"  Status: {status3}, Body: {body3}")

print("Test 4: Invalid school_code")
status4, body4 = test_login({"school_code": "INVALID_SCHOOL_CODE", "email": "principal@vaagdevi.com", "password": "wrongpassword"})
print(f"  Status: {status4}, Body: {body4}")
