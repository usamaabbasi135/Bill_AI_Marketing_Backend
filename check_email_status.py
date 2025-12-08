"""
Check email sending status.
"""
import requests
import sys

BASE_URL = "http://localhost:5000"

def main():
    if len(sys.argv) < 4:
        print("Usage: python check_email_status.py <email> <password> <email_id>")
        return
    
    email = sys.argv[1]
    password = sys.argv[2]
    email_id = sys.argv[3]
    
    # Login
    login_url = f"{BASE_URL}/api/auth/login"
    response = requests.post(login_url, json={"email": email, "password": password}, timeout=10)
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token = response.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get email status
    email_url = f"{BASE_URL}/api/emails/{email_id}"
    response = requests.get(email_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json().get('email', {})
        print(f"\nEmail Status: {data.get('status')}")
        print(f"Subject: {data.get('subject')}")
        if data.get('status') == 'sent':
            print("✅ Email was sent successfully!")
        elif data.get('status') == 'failed':
            print(f"❌ Email sending failed")
        else:
            print("⏳ Email is still being processed...")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()

