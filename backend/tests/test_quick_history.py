"""
Quick test for assessment history endpoint
"""

import requests
import time

BASE_URL = "http://localhost:8001"
TIMESTAMP = str(int(time.time()))
TEST_EMAIL = f"quick_test+{TIMESTAMP}@example.com"

# Signup
print("Signing up...")
signup_data = {
    "email": TEST_EMAIL,
    "password": "Pass123!",
    "role": "learner",
    "first_name": "Quick",
    "last_name": "Test"
}

signup = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
if signup.status_code != 200:
    print(f"Error: {signup.json()}")
    exit()

token = signup.json()["access_token"]
print(f"✅ Signed up with token: {token[:20]}...")

# Get history
print("\nGetting assessment history...")
headers = {"Authorization": f"Bearer {token}"}

try:
    response = requests.get(
        f"{BASE_URL}/assessment/history/all",
        headers=headers,
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
