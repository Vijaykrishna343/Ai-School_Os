"""
Regression test for DEFECT-002:
Ensures /openapi.json endpoint generates valid OpenAPI 3.0 specification without 500 errors.
"""

def test_openapi_generation(client):
    res = client.get("/openapi.json")
    assert res.status_code == 200
    data = res.json()
    assert "openapi" in data
    assert "paths" in data
    assert "/health/live" in data["paths"]
    assert "/health/ready" in data["paths"]
    assert "/api/v1/auth/login" in data["paths"]
