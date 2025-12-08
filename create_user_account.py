"""
Create a user account for email sending.
"""
import requests
import sys

BASE_URL = "http://localhost:5000"

def main():
    print("\n" + "="*70)
    print("  Create User Account")
    print("="*70)
    
    if len(sys.argv) < 3:
        print("\n❌ Usage: python create_user_account.py <email> <password> [first_name] [last_name] [company_name]")
        print("\nExample:")
        print("  python create_user_account.py rajalazibzia32@gmail.com YourPassword")
        print("  python create_user_account.py rajalazibzia32@gmail.com YourPassword Raj Ali Zia")
        return
    
    email = sys.argv[1]
    password = sys.argv[2]
    first_name = sys.argv[3] if len(sys.argv) > 3 else "Raj"
    last_name = sys.argv[4] if len(sys.argv) > 4 else "Ali"
    company_name = sys.argv[5] if len(sys.argv) > 5 else "My Company"
    
    print(f"\n📝 Creating account...")
    print(f"   Email: {email}")
    print(f"   Name: {first_name} {last_name}")
    print(f"   Company: {company_name}")
    
    # Register user
    register_url = f"{BASE_URL}/api/auth/register"
    register_data = {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "company_name": company_name
    }
    
    try:
        response = requests.post(register_url, json=register_data, timeout=10)
        
        if response.status_code == 201:
            data = response.json()
            print("\n✅ Account created successfully!")
            print(f"   Email: {email}")
            print(f"   User ID: {data.get('user', {}).get('user_id')}")
            print(f"   Tenant ID: {data.get('tenant', {}).get('tenant_id')}")
            print("\n💡 You can now use these credentials to login and send emails!")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get('error', 'Unknown error')
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"\n⚠️  User already exists: {email}")
                print("💡 You can use this account to login directly!")
                print(f"   Email: {email}")
                print(f"   Password: {password}")
            else:
                print(f"\n❌ Registration failed: {error_msg}")
                print(f"Response: {response.text}")
        else:
            print(f"\n❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to Flask server.")
        print("💡 Make sure your Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

