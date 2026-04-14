"""
Week 2 Assessment Scoring Test Suite
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"
TIMESTAMP = str(int(time.time()))
TEST_EMAIL = f"teacher+{TIMESTAMP}@example.com"
TEST_PASSWORD = "Pass123!"


def signup_and_login():
    """Signup and login to get tokens"""
    print("\n=== Step 1: Signup & Login ===")
    
    # Signup
    signup_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "role": "teacher",
        "first_name": "Test",
        "last_name": "Teacher"
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
    if response.status_code != 200:
        print(f"❌ Signup failed: {response.json()}")
        return None, None
    
    result = response.json()
    user_id = result["user"]["id"]
    token = result["access_token"]
    print(f"✅ Signed up: {TEST_EMAIL}")
    print(f"   User ID: {user_id}")
    print(f"   Token: {token[:20]}...")
    
    return token, user_id


def create_assessment(token):
    """Create an assessment"""
    print("\n=== Step 2: Create Assessment ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    create_data = {
        "template_id": "tmpl_001",
        "title": "Business English Speaking Test",
        "description": "Test your business English speaking skills",
        "difficulty_level": "intermediate"
    }
    
    response = requests.post(
        f"{BASE_URL}/assessment/create",
        json=create_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Create assessment failed: {response.json()}")
        return None
    
    result = response.json()
    assessment_id = result["id"]
    print(f"✅ Assessment created")
    print(f"   Assessment ID: {assessment_id}")
    print(f"   Title: {result['title']}")
    print(f"   Status: {result['status']}")
    
    return assessment_id


def score_assessment(token, assessment_id):
    """Submit response and get score"""
    print("\n=== Step 3: Submit Response & Get Score ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Good response
    print("\n📝 Test 1: Good Response")
    response_data = {
        "assessment_id": assessment_id,
        "question_id": "q001",
        "response_text": "Good morning, I'm pleased to meet you. I work in the marketing department and I specialize in digital strategy. In my role, I focus on developing comprehensive marketing campaigns that target specific customer segments. I have extensive experience with data analytics and customer segmentation techniques. This allows me to create personalized strategies that yield measurable results for our clients."
    }
    
    response = requests.post(
        f"{BASE_URL}/assessment/score",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Score submission failed: {response.json()}")
        return
    
    result = response.json()
    print(f"✅ Response scored successfully")
    print(f"   Final Score: {result['final_score']}/100")
    print(f"   Quality Score: {result['quality_score']}/100")
    print(f"   Quality Decision: {result['quality_decision']}")
    print(f"   Rubric Applied: {result['rubric_applied']}")
    print(f"   Gates Passed: {', '.join(result['gates_passed'])}")
    print(f"   Gates Failed: {', '.join(result['gates_failed'])}")
    print(f"   Feedback: {result['feedback']}")
    
    # Poor response
    print("\n📝 Test 2: Poor Response (too short)")
    response_data_2 = {
        "assessment_id": assessment_id,
        "question_id": "q002",
        "response_text": "Hi."
    }
    
    response2 = requests.post(
        f"{BASE_URL}/assessment/score",
        json=response_data_2,
        headers=headers
    )
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"✅ Poor response scored")
        print(f"   Final Score: {result2['final_score']}/100")
        print(f"   Quality Decision: {result2['quality_decision']}")
        print(f"   Feedback: {result2['feedback']}")
    else:
        print(f"⚠️  Error: {response2.json()}")


def get_assessment_history(token):
    """Get assessment history"""
    print("\n=== Step 4: Get Assessment History ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/assessment/history/all",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Get history failed: {response.json()}")
        return
    
    result = response.json()
    print(f"✅ Assessment history retrieved")
    print(f"   Total Assessments: {result['total_assessments']}")
    print(f"   Completed: {result['completed_assessments']}")
    print(f"   Average Score: {result['average_score']:.2f}/100")
    print(f"   Recent Assessments: {len(result['recent_assessments'])}")


def main():
    print("=" * 80)
    print("WEEK 2: ASSESSMENT SCORING TEST SUITE")
    print("=" * 80)
    
    # Signup and login
    token, user_id = signup_and_login()
    if not token:
        return
    
    # Create assessment
    assessment_id = create_assessment(token)
    if not assessment_id:
        return
    
    # Score assessment
    score_assessment(token, assessment_id)
    
    # Get history
    get_assessment_history(token)
    
    print("\n" + "=" * 80)
    print("✅ WEEK 2 TEST SUITE COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
