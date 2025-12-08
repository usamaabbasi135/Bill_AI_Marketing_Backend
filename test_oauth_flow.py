"""
Complete OAuth flow test - handles state persistence issue.
This script will guide you through the complete flow.
"""
import requests
import time
import webbrowser

BASE_URL = "http://localhost:5000"

def main():
    print("\n" + "="*70)
    print("  Complete Google OAuth Flow Test")
    print("="*70)
    
    # Step 1: Login
    print("\n📝 Step 1: Login to get JWT token")
    email = input("Enter your email: ").strip()
    password = input("Enter your password: ").strip()
    
    login_url = f"{BASE_URL}/api/auth/login"
    response = requests.post(login_url, json={"email": email, "password": password}, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token = response.json().get('access_token')
    if not token:
        print("❌ No access token received")
        return
    
    print("✅ Login successful!")
    
    # Step 2: Get OAuth URL
    print("\n📝 Step 2: Getting OAuth authorization URL...")
    auth_url_endpoint = f"{BASE_URL}/api/auth/oauth/google/authorize"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(auth_url_endpoint, headers=headers, timeout=10)
    if response.status_code != 200:
        print(f"❌ Failed to get OAuth URL: {response.text}")
        return
    
    data = response.json()
    auth_url = data.get('authorization_url')
    state = data.get('state')
    
    print(f"✅ OAuth URL generated!")
    print(f"State: {state}")
    
    # Step 3: Open browser
    print("\n📝 Step 3: Opening browser for OAuth...")
    print("⚠️  IMPORTANT: Complete the OAuth flow quickly (within 10 minutes)")
    print("   The state will expire after 10 minutes.")
    
    input("Press Enter to open browser...")
    webbrowser.open(auth_url)
    
    # Step 4: Wait and check
    print("\n⏳ Waiting for you to complete OAuth flow...")
    print("   After you see the success page, come back here and press Enter.")
    input()
    
    # Step 5: Verify
    print("\n📝 Step 4: Verifying connection...")
    time.sleep(2)  # Give it a moment to save
    
    providers_url = f"{BASE_URL}/api/auth/oauth/providers"
    response = requests.get(providers_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        providers = data.get('providers', [])
        
        if providers:
            print("✅ OAuth connection successful!")
            for p in providers:
                print(f"\n   Email: {p.get('email')}")
                print(f"   Provider: {p.get('provider')}")
                print(f"   Active: {p.get('is_active')}")
        else:
            print("⚠️  No providers found. Possible issues:")
            print("   1. OAuth flow not completed")
            print("   2. State expired (took more than 10 minutes)")
            print("   3. Error during token exchange")
            print("\n   Check Flask app logs for details.")
    else:
        print(f"❌ Error checking providers: {response.status_code}")
        print(f"Response: {response.text}")
    
    print("\n" + "="*70)
    print("  Test Complete!")
    print("="*70)

if __name__ == "__main__":
    main()

