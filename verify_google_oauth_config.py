"""
Verify Google OAuth configuration.
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*70)
print("  Google OAuth Configuration Check")
print("="*70)

client_id = os.getenv('GOOGLE_CLIENT_ID')
client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/auth/oauth/google/callback')

print("\n📋 Current Configuration:")
print(f"  GOOGLE_CLIENT_ID: {client_id[:30] + '...' if client_id and len(client_id) > 30 else client_id or 'NOT SET'}")
print(f"  GOOGLE_CLIENT_SECRET: {'SET' if client_secret else 'NOT SET'}")
print(f"  GOOGLE_REDIRECT_URI: {redirect_uri}")

print("\n✅ Checklist:")
issues = []

if not client_id:
    print("  ❌ GOOGLE_CLIENT_ID is not set")
    issues.append("Set GOOGLE_CLIENT_ID in .env file")
else:
    print("  ✅ GOOGLE_CLIENT_ID is set")

if not client_secret:
    print("  ❌ GOOGLE_CLIENT_SECRET is not set")
    issues.append("Set GOOGLE_CLIENT_SECRET in .env file")
else:
    print("  ✅ GOOGLE_CLIENT_SECRET is set")

if not redirect_uri:
    print("  ❌ GOOGLE_REDIRECT_URI is not set")
    issues.append("Set GOOGLE_REDIRECT_URI in .env file")
else:
    print("  ✅ GOOGLE_REDIRECT_URI is set")

print("\n🔍 Common Issues:")
print("  1. Redirect URI must match EXACTLY in Google Cloud Console")
print("     - No trailing slashes")
print("     - Exact case matching")
print("     - Must be: http://localhost:5000/api/auth/oauth/google/callback")
print("\n  2. Client Secret might be wrong")
print("     - Check if you copied it correctly")
print("     - Client secrets are only shown once when created")
print("     - If lost, create new credentials in Google Cloud Console")
print("\n  3. OAuth code can only be used once")
print("     - If you refresh the callback page, it will fail")
print("     - Start a new OAuth flow if code is expired")

if issues:
    print("\n❌ Issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n✅ Configuration looks good!")
    print("\n📝 Next steps:")
    print("  1. Go to Google Cloud Console")
    print("  2. Check that redirect URI matches exactly:")
    print(f"     {redirect_uri}")
    print("  3. Verify client ID and secret are correct")
    print("  4. Try OAuth flow again")

print("\n" + "="*70)

