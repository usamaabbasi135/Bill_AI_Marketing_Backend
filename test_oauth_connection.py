"""
Test script for Google OAuth connection and email sending.

This script helps test the OAuth integration step by step.
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"
# You'll need to replace this with a valid JWT token
# Get it by logging in via your auth endpoint
JWT_TOKEN = None  # Replace with your actual JWT token

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_google_authorize():
    """Test getting Google OAuth authorization URL."""
    print_section("Step 1: Get Google OAuth Authorization URL")
    
    if not JWT_TOKEN:
        print("❌ ERROR: JWT_TOKEN not set!")
        print("   Please set JWT_TOKEN in this script first.")
        print("   Get a token by logging in via: POST /api/auth/login")
        return None
    
    url = f"{BASE_URL}/api/auth/oauth/google/authorize"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Requesting: GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Authorization URL: {data.get('authorization_url')}")
            print(f"State: {data.get('state')}")
            print("\n📋 Next steps:")
            print("1. Copy the authorization_url above")
            print("2. Open it in your browser")
            print("3. Sign in with your Google account")
            print("4. Allow the permissions")
            print("5. You'll be redirected back to the callback URL")
            return data.get('authorization_url')
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Flask app!")
        print("   Make sure Flask app is running on http://localhost:5000")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_list_providers():
    """Test listing connected OAuth providers."""
    print_section("Step 2: List Connected OAuth Providers")
    
    if not JWT_TOKEN:
        print("❌ ERROR: JWT_TOKEN not set!")
        return None
    
    url = f"{BASE_URL}/api/auth/oauth/providers"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Requesting: GET {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            providers = data.get('providers', [])
            
            if providers:
                print("✅ Connected providers found:")
                for provider in providers:
                    print(f"  - Email: {provider.get('email')}")
                    print(f"    Provider: {provider.get('provider')}")
                    print(f"    Provider ID: {provider.get('provider_id')}")
                    print(f"    Active: {provider.get('is_active')}")
                    print()
                return True
            else:
                print("⚠️  No providers connected yet.")
                print("   Complete the OAuth flow first (Step 1)")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Flask app!")
        print("   Make sure Flask app is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_send_email(email_id):
    """Test sending an email via OAuth."""
    print_section("Step 3: Send Test Email")
    
    if not JWT_TOKEN:
        print("❌ ERROR: JWT_TOKEN not set!")
        return False
    
    if not email_id:
        print("⚠️  No email_id provided. Skipping email send test.")
        print("   Create an email first via: POST /api/emails/generate")
        return False
    
    url = f"{BASE_URL}/api/emails/{email_id}/send"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Requesting: POST {url}")
        response = requests.post(url, headers=headers, timeout=30)
        
        if response.status_code == 202:
            data = response.json()
            print("✅ Email sending started!")
            print(f"Job ID: {data.get('job_id')}")
            print(f"Email ID: {data.get('email_id')}")
            print("\n📧 The email will be sent via:")
            print("   1. Google OAuth (if connected)")
            print("   2. AWS SES (as fallback)")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Flask app!")
        print("   Make sure Flask app is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main test function."""
    print("\n" + "="*60)
    print("  Google OAuth Connection Test")
    print("="*60)
    
    if not JWT_TOKEN:
        print("\n⚠️  WARNING: JWT_TOKEN not set in script!")
        print("\nTo get a JWT token:")
        print("1. Start your Flask app")
        print("2. Login via: POST /api/auth/login")
        print("3. Copy the 'access_token' from response")
        print("4. Update JWT_TOKEN in this script")
        print("\nOr run this script with a token:")
        print("  python test_oauth_connection.py <your_jwt_token>")
        
        if len(sys.argv) > 1:
            global JWT_TOKEN
            JWT_TOKEN = sys.argv[1]
            print(f"\n✅ Using token from command line argument")
        else:
            print("\n❌ Cannot proceed without JWT token")
            return
    
    # Test 1: Get authorization URL
    auth_url = test_google_authorize()
    
    if auth_url:
        print("\n" + "-"*60)
        print("⏸️  PAUSE: Complete OAuth flow in browser")
        print("   Then press Enter to continue testing...")
        input()
    
    # Test 2: List providers
    has_provider = test_list_providers()
    
    # Test 3: Send email (optional)
    if has_provider:
        print("\n" + "-"*60)
        email_id = input("Enter an email_id to test sending (or press Enter to skip): ").strip()
        if email_id:
            test_send_email(email_id)
    
    print("\n" + "="*60)
    print("  Test Complete!")
    print("="*60)

if __name__ == "__main__":
    main()

