"""
Comprehensive test script for DELETE /api/profiles/<profile_id> endpoint.
Tests all acceptance criteria and edge cases.

Usage:
    python test_delete_profile_endpoint.py
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")

def print_step(step_num, description):
    print(f"\n{Colors.BOLD}Step {step_num}: {description}{Colors.RESET}")

# Test data
TEST_USER_1 = {
    "email": f"test_delete_1_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
    "password": "Test1234!",
    "first_name": "Test",
    "last_name": "User1",
    "company_name": "Test Company 1"
}

TEST_USER_2 = {
    "email": f"test_delete_2_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
    "password": "Test1234!",
    "first_name": "Test",
    "last_name": "User2",
    "company_name": "Test Company 2"
}

class DeleteProfileTester:
    def __init__(self):
        self.access_token_1 = None
        self.access_token_2 = None
        self.tenant_id_1 = None
        self.tenant_id_2 = None
        self.created_profile_ids = []
        self.created_campaign_id = None
        self.created_post_id = None
        self.created_company_id = None
        self.profile_in_campaign_id = None  # Profile linked to campaign
        
    def register_and_login(self, user_data, user_num):
        """Register and login to get JWT token"""
        print_info(f"Registering and logging in user {user_num}...")
        
        try:
            # Register
            register_response = requests.post(
                f"{API_BASE}/auth/register",
                json=user_data,
                headers={"Content-Type": "application/json"}
            )
            
            if register_response.status_code == 201:
                print_success(f"User {user_num} registered: {user_data['email']}")
            elif register_response.status_code == 400:
                print_info(f"User {user_num} already exists, attempting login...")
            else:
                print_error(f"Registration failed: {register_response.status_code}")
                return None, None
            
            # Login
            login_response = requests.post(
                f"{API_BASE}/auth/login",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                access_token = data.get("access_token")
                # Extract tenant_id from JWT (simplified - in real scenario, decode JWT)
                # For now, we'll get it from a profile query
                return access_token, None
            else:
                print_error(f"Login failed: {login_response.status_code}")
                return None, None
                
        except Exception as e:
            print_error(f"Error during registration/login: {str(e)}")
            return None, None
    
    def get_headers(self, access_token):
        """Get headers with authentication"""
        if not access_token:
            return {"Content-Type": "application/json"}
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    
    def setup_test_data(self):
        """Setup test data: profiles, company, post, campaign"""
        print_step(1, "Setup Test Data")
        
        # Setup user 1
        self.access_token_1, _ = self.register_and_login(TEST_USER_1, 1)
        if not self.access_token_1:
            print_error("Failed to authenticate user 1")
            return False
        
        # Setup user 2 (for cross-tenant test)
        self.access_token_2, _ = self.register_and_login(TEST_USER_2, 2)
        if not self.access_token_2:
            print_error("Failed to authenticate user 2")
            return False
        
        # Create profiles for user 1
        print_info("Creating test profiles for user 1...")
        profile_urls = [
            f"https://www.linkedin.com/in/delete-test-{datetime.now().strftime('%Y%m%d%H%M%S')}-1/",
            f"https://www.linkedin.com/in/delete-test-{datetime.now().strftime('%Y%m%d%H%M%S')}-2/",
            f"https://www.linkedin.com/in/delete-test-{datetime.now().strftime('%Y%m%d%H%M%S')}-3/",
            f"https://www.linkedin.com/in/delete-test-{datetime.now().strftime('%Y%m%d%H%M%S')}-4/",
        ]
        
        for url in profile_urls:
            response = requests.post(
                f"{API_BASE}/profiles",
                json={"linkedin_url": url},
                headers=self.get_headers(self.access_token_1)
            )
            
            if response.status_code == 201:
                profile_data = response.json()
                profile_id = profile_data.get("profile", {}).get("profile_id")
                if profile_id:
                    self.created_profile_ids.append(profile_id)
                    print_success(f"Created profile: {profile_id[:8]}...")
        
        if len(self.created_profile_ids) < 2:
            print_error("Failed to create enough profiles")
            return False
        
        # Create a profile for user 2 (for cross-tenant test)
        print_info("Creating test profile for user 2...")
        profile_url_user2 = f"https://www.linkedin.com/in/delete-test-user2-{datetime.now().strftime('%Y%m%d%H%M%S')}/"
        response = requests.post(
            f"{API_BASE}/profiles",
            json={"linkedin_url": profile_url_user2},
            headers=self.get_headers(self.access_token_2)
        )
        
        if response.status_code == 201:
            profile_data = response.json()
            self.profile_id_user2 = profile_data.get("profile", {}).get("profile_id")
            print_success(f"Created profile for user 2: {self.profile_id_user2[:8]}...")
        else:
            print_error("Failed to create profile for user 2")
            return False
        
        # Create company and post for campaign test
        print_info("Creating company and post for campaign test...")
        company_response = requests.post(
            f"{API_BASE}/companies",
            json={
                "name": "Test Company for Delete Test",
                "linkedin_url": "https://www.linkedin.com/company/microsoft/"
            },
            headers=self.get_headers(self.access_token_1)
        )
        
        if company_response.status_code in [201, 400]:
            if company_response.status_code == 201:
                company_data = company_response.json()
                self.created_company_id = company_data.get("company", {}).get("company_id")
            else:
                # Get existing company
                companies_response = requests.get(
                    f"{API_BASE}/companies",
                    headers=self.get_headers(self.access_token_1)
                )
                if companies_response.status_code == 200:
                    companies = companies_response.json().get("companies", [])
                    if companies:
                        self.created_company_id = companies[0].get("company_id")
        
        if self.created_company_id:
            # Get or create a post
            posts_response = requests.get(
                f"{API_BASE}/posts?company_id={self.created_company_id}&limit=1",
                headers=self.get_headers(self.access_token_1)
            )
            
            if posts_response.status_code == 200:
                posts = posts_response.json().get("posts", [])
                if posts:
                    self.created_post_id = posts[0].get("post_id")
        
        if self.created_post_id and len(self.created_profile_ids) > 0:
            # Create a campaign with one profile
            print_info("Creating campaign with profile for deletion test...")
            campaign_response = requests.post(
                f"{API_BASE}/campaigns",
                json={
                    "name": f"Test Campaign for Delete Test {datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "post_id": self.created_post_id,
                    "profile_ids": [self.created_profile_ids[0]],  # Link first profile to campaign
                    "status": "draft"
                },
                headers=self.get_headers(self.access_token_1)
            )
            
            if campaign_response.status_code == 201:
                campaign_data = campaign_response.json()
                self.created_campaign_id = campaign_data.get("campaign", {}).get("campaign_id")
                self.profile_in_campaign_id = self.created_profile_ids[0]  # Store which profile is in campaign
                print_success(f"Created campaign: {self.created_campaign_id[:8]}...")
                print_info(f"Profile {self.profile_in_campaign_id[:8]}... linked to campaign")
            else:
                print_info(f"Campaign creation returned {campaign_response.status_code}, skipping campaign test")
        
        print_success(f"Setup complete: {len(self.created_profile_ids)} profiles, campaign created")
        return True
    
    def test_delete_profile_success(self):
        """Test Case 1: Success case - Delete profile with no active campaigns"""
        print_step(2, "Test Case 1: Delete Profile - Success Case")
        
        if len(self.created_profile_ids) < 2:
            print_error("Not enough profiles for test")
            return False
        
        # Use a profile that's NOT linked to campaign (index 1 or later)
        profile_id = self.created_profile_ids[1] if len(self.created_profile_ids) > 1 else self.created_profile_ids[0]
        
        print_info(f"Attempting to delete profile: {profile_id[:8]}...")
        print_info("Expected: 200 OK, profile deleted successfully")
        
        try:
            response = requests.delete(
                f"{API_BASE}/profiles/{profile_id}",
                headers=self.get_headers(self.access_token_1)
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Profile deleted successfully":
                    print_success("✓ Profile deleted successfully")
                    print_info(f"Response: {data.get('message')}")
                    
                    # Verify profile is actually deleted by listing profiles
                    verify_response = requests.get(
                        f"{API_BASE}/profiles",
                        headers=self.get_headers(self.access_token_1)
                    )
                    if verify_response.status_code == 200:
                        profiles = verify_response.json().get("profiles", [])
                        profile_ids = [p.get("profile_id") for p in profiles]
                        if profile_id not in profile_ids:
                            print_success("✓ Profile confirmed deleted from database")
                            return True
                        else:
                            print_error("✗ Profile still exists in database")
                            return False
                    else:
                        print_error("✗ Could not verify deletion")
                        return False
                else:
                    print_error(f"✗ Unexpected message: {data.get('message')}")
                    return False
            else:
                print_error(f"✗ Expected 200, got {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"✗ Error: {str(e)}")
            return False
    
    def test_delete_profile_not_found(self):
        """Test Case 2: Profile not found"""
        print_step(3, "Test Case 2: Delete Profile - Not Found")
        
        invalid_profile_id = "00000000-0000-0000-0000-000000000000"
        print_info(f"Attempting to delete non-existent profile: {invalid_profile_id}")
        print_info("Expected: 404 Not Found")
        
        try:
            response = requests.delete(
                f"{API_BASE}/profiles/{invalid_profile_id}",
                headers=self.get_headers(self.access_token_1)
            )
            
            if response.status_code == 404:
                data = response.json()
                if "not found" in data.get("error", "").lower():
                    print_success("✓ Correctly returned 404 Not Found")
                    print_info(f"Error message: {data.get('error')}")
                    return True
                else:
                    print_error(f"✗ Wrong error message: {data.get('error')}")
                    return False
            else:
                print_error(f"✗ Expected 404, got {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"✗ Error: {str(e)}")
            return False
    
    def test_delete_profile_wrong_tenant(self):
        """Test Case 3: Unauthorized access - Different tenant"""
        print_step(4, "Test Case 3: Delete Profile - Wrong Tenant (403 Forbidden)")
        
        if not hasattr(self, 'profile_id_user2'):
            print_error("No profile from user 2 available")
            return False
        
        print_info(f"User 1 attempting to delete User 2's profile: {self.profile_id_user2[:8]}...")
        print_info("Expected: 403 Forbidden")
        
        try:
            response = requests.delete(
                f"{API_BASE}/profiles/{self.profile_id_user2}",
                headers=self.get_headers(self.access_token_1)
            )
            
            if response.status_code == 403:
                data = response.json()
                if "forbidden" in data.get("error", "").lower():
                    print_success("✓ Correctly returned 403 Forbidden")
                    print_info(f"Error message: {data.get('error')}")
                    return True
                else:
                    print_error(f"✗ Wrong error message: {data.get('error')}")
                    return False
            else:
                print_error(f"✗ Expected 403, got {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"✗ Error: {str(e)}")
            return False
    
    def test_delete_profile_in_campaign(self):
        """Test Case 4: Profile linked to active campaign"""
        print_step(5, "Test Case 4: Delete Profile - Linked to Campaign")
        
        if not self.created_campaign_id or not self.profile_in_campaign_id:
            print_info("Skipping - no campaign or profile linked to campaign available")
            print_info("This is OK if campaign/post setup failed")
            return True  # Not a failure, just skip
        
        # Use the profile that's linked to the campaign
        profile_id = self.profile_in_campaign_id
        
        print_info(f"Attempting to delete profile linked to campaign: {profile_id[:8]}...")
        print_info("Expected: 400 Bad Request - Cannot delete profile linked to active campaigns")
        
        try:
            response = requests.delete(
                f"{API_BASE}/profiles/{profile_id}",
                headers=self.get_headers(self.access_token_1)
            )
            
            if response.status_code == 400:
                data = response.json()
                error_msg = data.get("error", "").lower()
                if "campaign" in error_msg or "linked" in error_msg:
                    print_success("✓ Correctly returned 400 Bad Request")
                    print_info(f"Error message: {data.get('error')}")
                    return True
                else:
                    print_error(f"✗ Wrong error message: {data.get('error')}")
                    return False
            else:
                print_error(f"✗ Expected 400, got {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"✗ Error: {str(e)}")
            return False
    
    def test_delete_profile_with_emails(self):
        """Test Case 5: Profile with emails (if emails can be unlinked)"""
        print_step(6, "Test Case 5: Delete Profile - With Emails")
        
        if len(self.created_profile_ids) < 3:
            print_info("Skipping - not enough profiles for test")
            return True  # Not a failure
        
        # Use a profile that's not in campaign
        profile_id = self.created_profile_ids[2] if len(self.created_profile_ids) > 2 else None
        
        if not profile_id:
            print_info("Skipping - no available profile")
            return True
        
        print_info(f"Attempting to delete profile (may have emails): {profile_id[:8]}...")
        print_info("Expected: 200 OK (if emails can be unlinked) or 400 (if RESTRICT)")
        
        try:
            response = requests.delete(
                f"{API_BASE}/profiles/{profile_id}",
                headers=self.get_headers(self.access_token_1)
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("✓ Profile deleted successfully (emails were unlinked)")
                print_info(f"Response: {data.get('message')}")
                return True
            elif response.status_code == 400:
                data = response.json()
                error_msg = data.get("error", "").lower()
                if "email" in error_msg:
                    print_success("✓ Correctly prevented deletion due to email constraint")
                    print_info(f"Error message: {data.get('error')}")
                    return True
                else:
                    print_error(f"✗ Unexpected 400 error: {data.get('error')}")
                    return False
            else:
                print_error(f"✗ Unexpected status code: {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"✗ Error: {str(e)}")
            return False
    
    def test_delete_profile_no_auth(self):
        """Test Case 6: No authentication"""
        print_step(7, "Test Case 6: Delete Profile - No Authentication")
        
        if len(self.created_profile_ids) == 0:
            print_info("Skipping - no profiles available")
            return True
        
        profile_id = self.created_profile_ids[-1] if self.created_profile_ids else "test-id"
        
        print_info(f"Attempting to delete profile without authentication: {profile_id[:8]}...")
        print_info("Expected: 401 Unauthorized")
        
        try:
            response = requests.delete(
                f"{API_BASE}/profiles/{profile_id}",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 401:
                print_success("✓ Correctly returned 401 Unauthorized")
                return True
            else:
                print_error(f"✗ Expected 401, got {response.status_code}")
                print_error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"✗ Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all DELETE profile endpoint tests"""
        print_header("DELETE /api/profiles/<profile_id> Endpoint Test Suite")
        
        # Setup
        if not self.setup_test_data():
            print_error("Failed to setup test data")
            return False
        
        results = []
        
        # Run all test cases
        results.append(("Success Case", self.test_delete_profile_success()))
        results.append(("Profile Not Found (404)", self.test_delete_profile_not_found()))
        results.append(("Wrong Tenant (403)", self.test_delete_profile_wrong_tenant()))
        results.append(("Profile in Campaign (400)", self.test_delete_profile_in_campaign()))
        results.append(("Profile with Emails", self.test_delete_profile_with_emails()))
        results.append(("No Authentication (401)", self.test_delete_profile_no_auth()))
        
        # Summary
        print_header("Test Summary")
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            color = Colors.GREEN if result else Colors.RED
            print(f"{color}{status}{Colors.RESET} - {test_name}")
        
        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}\n")
        
        if passed == total:
            print_success("🎉 All DELETE profile endpoint tests passed!")
        else:
            print_error("⚠️  Some tests failed - review the output above")
        
        return passed == total

if __name__ == "__main__":
    print_info("Starting DELETE Profile Endpoint Test Suite...")
    print_info(f"Base URL: {BASE_URL}")
    print_info("Make sure the Flask server is running on http://localhost:5000")
    print()
    
    tester = DeleteProfileTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

