"""
Test script to verify standardized error response format
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_unauthenticated_access():
    """Test accessing protected endpoint without authentication"""
    print("\n=== Test 1: Unauthenticated Access ===")
    response = requests.get(f"{BASE_URL}/documents")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Verify response format
    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert data["status"] == "error", f"Expected status='error', got '{data['status']}'"
    assert "message" in data, "Response missing 'message' field"
    assert "error_code" in data, "Response missing 'error_code' field"
    print("✓ Response format is correct!")

def test_invalid_token():
    """Test accessing protected endpoint with invalid token"""
    print("\n=== Test 2: Invalid Token ===")
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = requests.get(f"{BASE_URL}/documents", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Verify response format
    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert data["status"] == "error", f"Expected status='error', got '{data['status']}'"
    assert "message" in data, "Response missing 'message' field"
    assert "error_code" in data, "Response missing 'error_code' field"
    print("✓ Response format is correct!")

def test_successful_endpoint():
    """Test a successful endpoint (root)"""
    print("\n=== Test 3: Successful Endpoint ===")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Verify response format
    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert data["status"] == "success", f"Expected status='success', got '{data['status']}'"
    assert "message" in data, "Response missing 'message' field"
    print("✓ Response format is correct!")

if __name__ == "__main__":
    try:
        test_unauthenticated_access()
        test_invalid_token()
        test_successful_endpoint()
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
