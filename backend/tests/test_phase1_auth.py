"""
Phase 1 Auth Testing - Test signup, login, verify token
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8001"

# Use unique email for each test run
TIMESTAMP = str(int(time.time()))
TEST_EMAIL = f"testlearner+{TIMESTAMP}@example.com"
TEST_PASSWORD = "Pass123!"

def test_signup():
    """Test user signup"""
    print("\n=== Testing Signup ===")
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "role": "learner",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup",
            json=signup_data,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            return result.get("access_token"), result.get("user")
        return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None


def test_login(email, password):
    """Test user login"""
    print("\n=== Testing Login ===")
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            return result.get("access_token"), result.get("refresh_token")
        return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None


def test_verify_token(token):
    """Test token verification"""
    print("\n=== Testing Token Verify ===")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/verify",
            headers=headers,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_orchestrate(token, event_type):
    """Test orchestration endpoint"""
    print(f"\n=== Testing Orchestrate ({event_type}) ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "event_type": event_type,
        "payload": {
            "test": True
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/orchestrate",
            json=payload,
            headers=headers,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    print("🚀 Phase 1 Auth & Orchestration Test Suite")
    
    # Test signup
    token, user = test_signup()
    if not token:
        print("❌ Signup failed")
        return
    
    print(f"✅ Signup successful: {user.get('email')}")
    print(f"   Access Token: {token[:20]}...")
    
    # Test token verify
    if test_verify_token(token):
        print("✅ Token verification successful")
    else:
        print("❌ Token verification failed")
        return
    
    # Test login
    access_token, refresh_token = test_login(TEST_EMAIL, TEST_PASSWORD)
    if not access_token:
        print("❌ Login failed")
        return
    
    print("✅ Login successful")
    print(f"   New Access Token: {access_token[:20]}...")
    
    # Test orchestrate with different event types
    test_events = [
        "validate_item",
        "score_assessment",
        "create_screening_pack",
    ]
    
    for event in test_events:
        if test_orchestrate(access_token, event):
            print(f"✅ Orchestrate event '{event}' successful")
        else:
            print(f"❌ Orchestrate event '{event}' failed")
    
    print("\n✅ Phase 1 Test Suite Complete!")


if __name__ == "__main__":
    main()
