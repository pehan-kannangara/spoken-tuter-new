"""
Quick Manual Testing Guide for Phase 1 API
"""

import requests
import json

BASE_URL = "http://localhost:8001"

print("=" * 80)
print("PHASE 1 API MANUAL TESTING GUIDE")
print("=" * 80)

# 1. Get API Documentation
print("\n1️⃣  OPENAPI DOCUMENTATION")
print("   Open in browser: http://localhost:8001/docs")
print("   This shows all endpoints with interactive testing!\n")

# 2. Health check
print("2️⃣  HEALTH CHECK")
health = requests.get(f"{BASE_URL}/health")
print(f"   GET {BASE_URL}/health")
print(f"   Status: {health.status_code}")
print(f"   Response: {json.dumps(health.json(), indent=2)}\n")

# 3. Signup example
print("3️⃣  SIGNUP EXAMPLE")
print(f"   POST {BASE_URL}/auth/signup")
print("""
   {
     "email": "user@example.com",
     "password": "SecurePass123",
     "role": "learner",
     "first_name": "Jane",
     "last_name": "Smith"
   }
   """)

# 4. Login example
print("4️⃣  LOGIN EXAMPLE")
print(f"   POST {BASE_URL}/auth/login")
print("""
   {
     "email": "user@example.com",
     "password": "SecurePass123"
   }
   """)

# 5. Verify token using curl
print("5️⃣  VERIFY TOKEN (with curl)")
print(f"""
   curl -X GET "{BASE_URL}/auth/verify" \\
     -H "Authorization: Bearer <your_access_token>"
   """)

# 6. Orchestrate endpoint
print("6️⃣  ORCHESTRATE ENDPOINT (Main router)")
print(f"   POST {BASE_URL}/orchestrate")
print("""
   Headers: Authorization: Bearer <your_access_token>
   
   Body:
   {
     "event_type": "validate_item",
     "payload": {
       "item_id": "q123"
     }
   }
   
   Supported event_types:
   - validate_item        → routes to qa_workflow
   - score_assessment     → routes to assessment_scoring
   - generate_feedback    → routes to feedback_pathway
   - create_screening_pack → routes to recruiter_screening
   """)

# 7. Testing endpoints with PowerShell
print("7️⃣  TEST WITH POWERSHELL")
print("""
   $auth = @{
       email = "test@example.com"
       password = "Pass123!"
   } | ConvertTo-Json
   
   $signup = Invoke-WebRequest -Uri "http://localhost:8001/auth/signup" \\
       -Method POST \\
       -Headers @{"Content-Type"="application/json"} \\
       -Body $auth
   
   $signup.Content | ConvertFrom-Json | ConvertTo-Json
   """)

print("\n" + "=" * 80)
print("✅ API IS RUNNING AND READY FOR TESTING!")
print("=" * 80)
