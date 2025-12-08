"""
Connect your Google account for OAuth email sending.
"""
import requests
import sys
import webbrowser
import time

BASE_URL = "http://localhost:5000"

def main():
    print("\n" + "="*70)
    print("  Connect Google OAuth Account")
    print("="*70)
    
    if len(sys.argv) < 3:
        print("\n❌ Usage: python connect_google_oauth.py <email> <password>")
        print("\nExample:")
        print("  python connect_google_oauth.py rajalazibzia32@gmail.com YourPassword")
        return
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    # Step 1: Login
    print(f"\n📝 Step 1: Logging in as {email}...")
    login_url = f"{BASE_URL}/api/auth/login"
    response = requests.post(login_url, json={"email": email, "password": password}, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        print("\n💡 Make sure you've created an account first:")
        print("   python create_user_account.py <email> <password>")
        return
    
    token = response.json().get('access_token')
    if not token:
        print("❌ No access token received")
        return
    
    print("✅ Login successful!")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Check if already connected
    print("\n📝 Step 2: Checking existing OAuth connections...")
    providers_url = f"{BASE_URL}/api/auth/oauth/providers"
    response = requests.get(providers_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        providers = data.get('providers', [])
        google_providers = [p for p in providers if p.get('provider') == 'google']
        
        if google_providers:
            print("✅ Google OAuth already connected:")
            for p in google_providers:
                print(f"   - Email: {p.get('email')}")
                print(f"   - Provider ID: {p.get('provider_id')}")
                print(f"   - Created: {p.get('created_at')}")
            
            print("\n💡 You can use this connection to send emails!")
            print("💡 If you want to reconnect, disconnect first or use a different account.")
            return
    
    # Step 3: Get OAuth authorization URL
    print("\n📝 Step 3: Getting Google OAuth authorization URL...")
    auth_url_endpoint = f"{BASE_URL}/api/auth/oauth/google/authorize"
    
    try:
        response = requests.get(auth_url_endpoint, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed to get authorization URL: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        data = response.json()
        authorization_url = data.get('authorization_url')
        state = data.get('state')
        
        if not authorization_url:
            print("❌ No authorization URL received")
            print(f"Response: {data}")
            return
        
        print("✅ Authorization URL generated!")
        print(f"\n📋 Authorization URL:")
        print(f"   {authorization_url}")
        
        # Step 4: Open in browser
        print("\n📝 Step 4: Opening browser for OAuth authorization...")
        print("   Please complete the OAuth flow in your browser.")
        print("   You'll need to:")
        print("   1. Sign in with your Google account (rajalazibzia32@gmail.com)")
        print("   2. Grant permissions to send emails")
        print("   3. You'll be redirected back with a success message")
        
        try:
            webbrowser.open(authorization_url)
            print("\n✅ Browser opened!")
        except Exception as e:
            print(f"\n⚠️  Could not open browser automatically: {str(e)}")
            print(f"   Please copy and paste this URL into your browser:")
            print(f"   {authorization_url}")
        
        # Step 5: Wait and verify
        print("\n⏳ Waiting for you to complete OAuth flow...")
        print("   (This may take 30-60 seconds)")
        print("   After you see the success page, press Enter here...")
        
        input("\n   Press Enter after completing OAuth in browser: ")
        
        # Step 6: Verify connection
        print("\n📝 Step 5: Verifying OAuth connection...")
        time.sleep(2)  # Give it a moment for the callback to process
        
        response = requests.get(providers_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            providers = data.get('providers', [])
            google_providers = [p for p in providers if p.get('provider') == 'google']
            
            if google_providers:
                print("✅ Google OAuth connected successfully!")
                for p in google_providers:
                    print(f"   - Email: {p.get('email')}")
                    print(f"   - Provider ID: {p.get('provider_id')}")
                    print(f"   - Created: {p.get('created_at')}")
                
                print("\n🎉 You can now send emails via OAuth!")
                print("💡 Run: python send_email_to_friend.py <email> <password>")
            else:
                print("⚠️  OAuth connection not found yet.")
                print("💡 Make sure you completed the OAuth flow in the browser.")
                print("💡 Check the browser for any error messages.")
        else:
            print(f"⚠️  Could not verify connection: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to Flask server.")
        print("💡 Make sure your Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

