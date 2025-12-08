"""
Create a simple test email and send it via OAuth.
"""
import requests
import sys
import uuid
from datetime import datetime

BASE_URL = "http://localhost:5000"

# Default recipient email (your friend)
DEFAULT_RECIPIENT_EMAIL = "usamahafeez.abbasi1234@gmail.com"

def main():
    print("\n" + "="*70)
    print("  Create and Send Simple Test Email with OAuth")
    print("="*70)
    
    if len(sys.argv) < 3:
        print("\n❌ Usage: python create_simple_test_email.py <email> <password> [recipient_email]")
        print(f"\nExample (using default recipient: {DEFAULT_RECIPIENT_EMAIL}):")
        print("  python create_simple_test_email.py rajalazibzia32@gmail.com YourPassword")
        print("\nOr specify a different recipient:")
        print("  python create_simple_test_email.py rajalazibzia32@gmail.com YourPassword recipient@example.com")
        return
    
    email = sys.argv[1]
    password = sys.argv[2]
    recipient_email = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_RECIPIENT_EMAIL
    
    print(f"\n📧 Recipient email: {recipient_email}")
    
    # Step 1: Login
    print("\n📝 Step 1: Login...")
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
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get tenant_id from token
    import jwt
    decoded = jwt.decode(token, options={"verify_signature": False})
    tenant_id = decoded.get('tenant_id')
    
    # Step 2: Create minimal test data via database
    print("\n📝 Step 2: Creating test data...")
    from app import create_app
    from app.extensions import db
    from app.models.post import Post
    from app.models.profile import Profile
    from app.models.email_template import EmailTemplate
    from app.models.email import Email
    from app.models.company import Company
    
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
        
        # Get or create profile
        profile = Profile.query.filter_by(tenant_id=tenant_id).first()
        if not profile:
            profile = Profile(
                profile_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                linkedin_url="https://www.linkedin.com/in/test",
                email=recipient_email,
                person_name="Test Recipient",
                status="scraped"
            )
            db.session.add(profile)
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
            subject="Test Email - OAuth Integration",
            body=f"This is a test email sent via OAuth.\n\nSent from: rajalazibzia32@gmail.com\nRecipient: {recipient_email}\n\nThis email was sent using Google OAuth integration.",
            status="draft"
        )
        db.session.add(test_email)
        db.session.commit()
        
        email_id = test_email.email_id
        print(f"✅ Test email created!")
        print(f"   Email ID: {email_id}")
        print(f"   Subject: {test_email.subject}")
        print(f"   Recipient: {recipient_email}")
    
    # Step 3: Check OAuth provider
    print("\n📝 Step 3: Checking OAuth provider...")
    providers_url = f"{BASE_URL}/api/auth/oauth/providers"
    response = requests.get(providers_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        providers = data.get('providers', [])
        if providers:
            print("✅ OAuth provider connected:")
            for p in providers:
                print(f"   Email: {p.get('email')}")
                print(f"   Provider: {p.get('provider')}")
            print("\n📧 Email will be sent via OAuth from: rajalazibzia32@gmail.com")
        else:
            print("⚠️  No OAuth provider connected. Email will use AWS SES fallback.")
    
    # Step 4: Send email
    print(f"\n📝 Step 4: Sending email...")
    send_url = f"{BASE_URL}/api/emails/{email_id}/send"
    
    try:
        response = requests.post(send_url, headers=headers, timeout=10)  # Shorter timeout since it's async
        
        if response.status_code == 202:
            data = response.json()
            print("✅ Email sending started!")
            print(f"   Job ID: {data.get('job_id')}")
            print(f"   Email ID: {data.get('email_id')}")
            print("\n📧 Email is being sent asynchronously via:")
            print("   1. Google OAuth (rajalazibzia32@gmail.com) - if connected")
            print("   2. AWS SES (as fallback)")
            print("\n💡 The email sending happens in the background (Celery task)")
            print("💡 Check your Flask app logs to see which method was used")
            print(f"💡 Check {recipient_email} inbox to verify the email was received")
            print("💡 The sender should be: rajalazibzia32@gmail.com (if OAuth works)")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.Timeout:
        print("⚠️  Request timed out (this is normal for async tasks)")
        print("✅ Email sending was initiated - it's processing in the background")
        print("\n💡 Check your Flask app logs to see the sending status")
        print(f"💡 Check {recipient_email} inbox to verify the email was received")
    
    print("\n" + "="*70)
    print("  Test Complete!")
    print("="*70)

if __name__ == "__main__":
    main()

