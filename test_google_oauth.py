"""
Quick test script for Google OAuth connection.
Run this after starting Flask app.
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def test_health():
    """Test if Flask app is running."""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask app is running")
            return True
        else:
            print(f"❌ Flask app returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Flask app: {e}")
        print("   Make sure Flask app is running: python run.py")
        return False

def get_jwt_token(email, password):
    """Login and get JWT token."""
    print_header("Step 1: Getting JWT Token")
    
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "email": email,
        "password": password
    }
    
    try:
        print(f"Logging in as: {email}")
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            token = result.get('access_token')
            if token:
                print("✅ Login successful!")
                print(f"Token: {token[:50]}...")
                return token
            else:
                print("❌ No access_token in response")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_google_authorize(token):
    """Test Google OAuth authorization."""
    print_header("Step 2: Get Google OAuth Authorization URL")
    
    url = f"{BASE_URL}/api/auth/oauth/google/authorize"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"Requesting: GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get('authorization_url')
            state = data.get('state')
            
            print("✅ Authorization URL generated!")
            print(f"\n📋 Authorization URL:")
            print(f"   {auth_url}")
            print(f"\n📋 State: {state}")
            print("\n" + "-"*70)
            print("📝 NEXT STEPS:")
            print("   1. Copy the Authorization URL above")
            print("   2. Open it in your browser")
            print("   3. Sign in with your Google account")
            print("   4. Click 'Allow' to grant permissions")
            print("   5. You'll be redirected back")
            print("-"*70)
            
            return auth_url
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_list_providers(token):
    """Test listing connected providers."""
    print_header("Step 3: Check Connected OAuth Providers")
    
    url = f"{BASE_URL}/api/auth/oauth/providers"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"Requesting: GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            providers = data.get('providers', [])
            
            if providers:
                print("✅ Connected providers found:")
                for p in providers:
                    print(f"\n   Email: {p.get('email')}")
                    print(f"   Provider: {p.get('provider')}")
                    print(f"   Provider ID: {p.get('provider_id')}")
                    print(f"   Active: {p.get('is_active')}")
                return True
            else:
                print("⚠️  No providers connected yet.")
                print("   Complete the OAuth flow in your browser first.")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_send_email(token, email_id):
    """Test sending an email."""
    print_header("Step 4: Send Test Email")
    
    if not email_id:
        print("⚠️  No email_id provided. Skipping email send test.")
        print("   To test email sending:")
        print("   1. Create an email via POST /api/emails/generate")
        print("   2. Get the email_id from the response")
        print("   3. Run this script with: python test_google_oauth.py <email> <password> <email_id>")
        return False
    
    url = f"{BASE_URL}/api/emails/{email_id}/send"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"Requesting: POST {url}")
        response = requests.post(url, headers=headers, timeout=30)
        
        if response.status_code == 202:
            data = response.json()
            print("✅ Email sending started!")
            print(f"   Job ID: {data.get('job_id')}")
            print(f"   Email ID: {data.get('email_id')}")
            print("\n📧 Email will be sent via:")
            print("   1. Google OAuth (if connected)")
            print("   2. AWS SES (as fallback)")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("  Google OAuth Connection Test")
    print("="*70)
    
    # Check if Flask is running
    if not test_health():
        return
    
    # Get credentials
    if len(sys.argv) < 3:
        print("\n❌ Usage: python test_google_oauth.py <email> <password> [email_id]")
        print("\nExample:")
        print("  python test_google_oauth.py user@example.com password123")
        print("  python test_google_oauth.py user@example.com password123 email-uuid-here")
        return
    
    email = sys.argv[1]
    password = sys.argv[2]
    email_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Step 1: Get JWT token
    token = get_jwt_token(email, password)
    if not token:
        return
    
    # Step 2: Get OAuth authorization URL
    auth_url = test_google_authorize(token)
    
    if auth_url:
        print("\n" + "="*70)
        print("⏸️  PAUSE: Complete OAuth flow in browser")
        print("="*70)
        input("Press Enter after completing OAuth flow to continue...")
    
    # Step 3: Check providers
    has_provider = test_list_providers(token)
    
    # Step 4: Test email sending
    if email_id:
        test_send_email(token, email_id)
    elif has_provider:
        print("\n💡 Tip: To test email sending, provide an email_id as the 3rd argument")
    
    print("\n" + "="*70)
    print("  Test Complete!")
    print("="*70)

if __name__ == "__main__":
    main()

