"""
Debug password hashing
"""

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4,
)

password = "Pass123!"
print(f"Password: '{password}'")
print(f"Password length (chars): {len(password)}")
print(f"Password length (bytes): {len(password.encode())}")

try:
    hashed = pwd_context.hash(password)
    print(f"✅ Hash successful: {hashed[:40]}...")
    
    # Test verification
    if pwd_context.verify(password, hashed):
        print(f"✅ Verification successful")
    else:
        print(f"❌ Verification failed")
except Exception as e:
    print(f"❌ Error: {e}")
