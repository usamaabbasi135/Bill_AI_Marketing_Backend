"""
Simple script to send an email to your friend using OAuth.
"""
import requests
import sys

BASE_URL = "http://localhost:5000"

# Default friend email
FRIEND_EMAIL = "usamahafeez.abbasi1234@gmail.com"

def main():
    print("\n" + "="*70)
    print("  Send Email to Friend via OAuth")
    print("="*70)
    
    if len(sys.argv) < 3:
        print("\n❌ Usage: python send_email_to_friend.py <your_email> <your_password> [friend_email]")
        print(f"\nExample (using default friend email: {FRIEND_EMAIL}):")
        print("  python send_email_to_friend.py rajalazibzia32@gmail.com YourPassword")
        print("\nOr specify a different friend email:")
        print("  python send_email_to_friend.py rajalazibzia32@gmail.com YourPassword friend@example.com")
        return
    
    your_email = sys.argv[1]
    your_password = sys.argv[2]
    # Use friend email from argument if provided, otherwise use default
    friend_email = sys.argv[3] if len(sys.argv) > 3 else FRIEND_EMAIL
    
    print(f"\n📧 Friend email: {friend_email}")
    
    # Step 1: Login
    print(f"\n📝 Step 1: Logging in as {your_email}...")
    login_url = f"{BASE_URL}/api/auth/login"
    response = requests.post(login_url, json={"email": your_email, "password": your_password}, timeout=10)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token = response.json().get('access_token')
    if not token:
        print("❌ No access token received")
        return
    
    print("✅ Login successful!")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Check OAuth connection
    print("\n📝 Step 2: Checking OAuth connection...")
    providers_url = f"{BASE_URL}/api/auth/oauth/providers"
    response = requests.get(providers_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        providers = data.get('providers', [])
        if providers:
            print("✅ OAuth provider connected:")
            for p in providers:
                print(f"   - Email: {p.get('email')}")
                print(f"   - Provider: {p.get('provider')}")
        else:
            print("⚠️  No OAuth provider connected. Email will use AWS SES fallback.")
    
    # Step 3: Create email using the existing script
    print(f"\n📝 Step 3: Creating email for {friend_email}...")
    print("   (Using create_simple_test_email.py functionality)")
    
    # Import the create_simple_test_email script's logic
    import uuid
    from app import create_app
    from app.extensions import db
    from app.models.post import Post
    from app.models.profile import Profile
    from app.models.email_template import EmailTemplate
    from app.models.email import Email
    from app.models.company import Company
    import jwt
    
    decoded = jwt.decode(token, options={"verify_signature": False})
    tenant_id = decoded.get('tenant_id')
    
    app = create_app()
    with app.app_context():
        # Get or create company
        company = Company.query.filter_by(tenant_id=tenant_id).first()
        if not company:
            company = Company(
                company_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name="Test Company",
                linkedin_url="https://www.linkedin.com/company/test",
                is_active=True
            )
            db.session.add(company)
            db.session.flush()
        
        # Get or create post
        post = Post.query.filter_by(tenant_id=tenant_id).first()
        if not post:
            post = Post(
                tenant_id=tenant_id,
                company_id=company.company_id,
                source_url="https://www.linkedin.com/feed/update/test-post",
                post_text="This is a test post for OAuth email sending."
            )
            db.session.add(post)
            db.session.flush()
        
        # Create or update profile with friend's email
        profile = Profile.query.filter_by(
            tenant_id=tenant_id,
            email=friend_email
        ).first()
        
        if not profile:
            profile = Profile(
                profile_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                linkedin_url="https://www.linkedin.com/in/friend",
                email=friend_email,
                person_name="Friend",
                status="scraped"
            )
            db.session.add(profile)
            db.session.flush()
        else:
            # Update email if it changed
            profile.email = friend_email
            db.session.flush()
        
        # Get template
        template = EmailTemplate.query.filter(
            (EmailTemplate.tenant_id == tenant_id) | (EmailTemplate.is_default == True)
        ).first()
        
        if not template:
            print("❌ No template found. Please create a template first.")
            return
        
        # Create email
        test_email = Email(
            email_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            post_id=post.post_id,
            profile_id=profile.profile_id,
            template_id=template.template_id,
            subject="Hello from OAuth Email!",
            body=f"""Hi there!

This is a test email sent to you via Gmail OAuth integration.

Sent from: {your_email}
Recipient: {friend_email}

This email was sent using Google OAuth integration, so it should appear in your inbox (or spam folder).

Best regards,
Your Friend
            """.strip(),
            status="draft"
        )
        db.session.add(test_email)
        db.session.commit()
        
        email_id = test_email.email_id
        print(f"✅ Email created!")
        print(f"   Email ID: {email_id}")
        print(f"   Subject: {test_email.subject}")
        print(f"   Recipient: {friend_email}")
    
    # Step 4: Send email
    print(f"\n📝 Step 4: Sending email to {friend_email}...")
    send_url = f"{BASE_URL}/api/emails/{email_id}/send"
    
    try:
        response = requests.post(send_url, headers=headers, timeout=10)
        
        if response.status_code == 202:
            data = response.json()
            print("✅ Email sending started!")
            print(f"   Job ID: {data.get('job_id')}")
            print(f"   Email ID: {data.get('email_id')}")
            print("\n📧 Email Details:")
            print(f"   From: {your_email} (via OAuth)")
            print(f"   To: {friend_email}")
            print(f"   Subject: Hello from OAuth Email!")
            print("\n💡 The email is being sent in the background")
            print(f"💡 Check {friend_email} inbox (and spam folder) to verify")
            print("💡 The sender should be: " + (providers[0].get('email') if providers else "AWS SES"))
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.Timeout:
        print("⚠️  Request timed out (this is normal for async tasks)")
        print("✅ Email sending was initiated - it's processing in the background")
        print(f"💡 Check {friend_email} inbox to verify the email was received")
    
    print("\n" + "="*70)
    print("  Complete!")
    print("="*70)

if __name__ == "__main__":
    main()

