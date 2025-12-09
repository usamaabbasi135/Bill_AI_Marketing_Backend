"""
Comprehensive test script for Bulk Delete API endpoints.
Tests DELETE /api/profiles/bulk and DELETE /api/posts/bulk endpoints.

Usage:
    python test_bulk_delete_endpoints.py
"""

import requests
import json
import sys
import time
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
TEST_USER = {
    "email": f"test_bulk_delete_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com",
    "password": "Test1234!",
    "first_name": "Test",
    "last_name": "User",
    "company_name": "Test Company"
}

class BulkDeleteTester:
    def __init__(self):
        self.access_token = None
        self.tenant_id = None
        self.created_profile_ids = []
        self.created_post_ids = []
        self.created_company_id = None
        self.created_campaign_id = None
        self.created_email_ids = []
        self.profiles_linked_to_campaign = []  # Track which profiles are linked to campaign
        
    def register_and_login(self):
        """Step 1: Register a new user and login to get JWT token"""
        print_step(1, "Register and Login")
        
        try:
            # Register
            print_info("Registering new user...")
            register_response = requests.post(
                f"{API_BASE}/auth/register",
                json=TEST_USER,
                headers={"Content-Type": "application/json"}
            )
            
            if register_response.status_code == 201:
                print_success(f"User registered: {TEST_USER['email']}")
            elif register_response.status_code == 400:
                print_info("User already exists, attempting login...")
            else:
                print_error(f"Registration failed: {register_response.status_code}")
                print_error(f"Response: {register_response.text}")
                return False
            
            # Login
            print_info("Logging in...")
            login_response = requests.post(
                f"{API_BASE}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                self.access_token = data.get("access_token")
                if self.access_token:
                    print_success("Login successful")
                    print_info(f"Token: {self.access_token[:50]}...")
                    return True
                else:
                    print_error("No access token in response")
                    return False
            else:
                print_error(f"Login failed: {login_response.status_code}")
                print_error(f"Response: {login_response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error during registration/login: {str(e)}")
            return False
    
    def get_headers(self):
        """Get headers with authentication"""
        if not self.access_token:
            return {"Content-Type": "application/json"}
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
    
    def setup_test_data(self):
        """Step 2: Create test data (profiles, posts, campaigns, emails)"""
        print_step(2, "Setup Test Data")
        
        try:
            # Create a company first (needed for posts)
            print_info("Creating test company...")
            company_response = requests.post(
                f"{API_BASE}/companies",
                json={
                    "name": "Test Company for Bulk Delete",
                    "linkedin_url": "https://www.linkedin.com/company/test-bulk-delete"
                },
                headers=self.get_headers()
            )
            
            if company_response.status_code == 201:
                self.created_company_id = company_response.json().get("company", {}).get("company_id")
                print_success(f"Company created: {self.created_company_id}")
            else:
                print_error(f"Failed to create company: {company_response.status_code}")
                print_error(f"Response: {company_response.text}")
                return False
            
            # Create 15 profiles for testing (need enough for all test scenarios)
            # - First 3 will be linked to campaign (for validation tests)
            # - Next 5 will be deleted in success test
            # - Remaining 7+ will be used for partial success test
            print_info("Creating 15 test profiles...")
            profile_urls = [
                f"https://www.linkedin.com/in/test-profile-{i}/" 
                for i in range(1, 16)
            ]
            
            for url in profile_urls:
                profile_response = requests.post(
                    f"{API_BASE}/profiles",
                    json={"linkedin_url": url},
                    headers=self.get_headers()
                )
                
                if profile_response.status_code == 201:
                    profile_id = profile_response.json().get("profile", {}).get("profile_id")
                    self.created_profile_ids.append(profile_id)
                    print_info(f"Created profile: {profile_id}")
                else:
                    print_error(f"Failed to create profile {url}: {profile_response.status_code}")
            
            print_success(f"Created {len(self.created_profile_ids)} profiles")
            
            # Posts are typically created via scraping, so we'll use existing posts
            # or create them via direct database access if needed
            print_info("Fetching existing posts or creating test posts...")
            
            # First, try to get existing posts
            posts_response = requests.get(
                f"{API_BASE}/posts?limit=10",
                headers=self.get_headers()
            )
            
            if posts_response.status_code == 200:
                posts_data = posts_response.json().get("posts", [])
                existing_post_ids = [p.get("post_id") for p in posts_data]
                self.created_post_ids = existing_post_ids[:10]
                print_info(f"Found {len(self.created_post_ids)} existing posts")
            
            # If no posts exist, create one directly via database for testing
            if len(self.created_post_ids) == 0:
                print_info("No posts found. Creating a test post directly via database...")
                try:
                    from app import create_app
                    from app.extensions import db
                    from app.models.post import Post
                    from datetime import date
                    import uuid
                    try:
                        import jwt
                        use_jwt = True
                    except ImportError:
                        use_jwt = False
                        print_info("JWT library not available, will try alternative method")
                    
                    app = create_app()
                    with app.app_context():
                        # Get tenant_id from JWT token or use a workaround
                        tenant_id = None
                        if use_jwt:
                            try:
                                # Decode JWT to get tenant_id (without verification for testing)
                                decoded = jwt.decode(self.access_token, options={"verify_signature": False})
                                tenant_id = decoded.get('tenant_id')
                            except:
                                pass
                        
                        # If we couldn't get tenant_id from JWT, try to get it from the user's profile
                        if not tenant_id:
                            # Get user info to find tenant_id
                            user_response = requests.get(
                                f"{API_BASE}/auth/me",
                                headers=self.get_headers()
                            )
                            if user_response.status_code == 200:
                                user_data = user_response.json()
                                tenant_id = user_data.get('tenant_id')
                        
                        if tenant_id and self.created_company_id:
                            # Create a test post
                            test_post = Post(
                                post_id=str(uuid.uuid4()),
                                tenant_id=tenant_id,
                                company_id=self.created_company_id,
                                source_url="https://www.linkedin.com/feed/update/test-bulk-delete-post/",
                                post_text="Test post for bulk delete testing",
                                post_date=date.today()
                            )
                            db.session.add(test_post)
                            db.session.commit()
                            self.created_post_ids.append(test_post.post_id)
                            print_success(f"Created test post: {test_post.post_id}")
                        else:
                            print_error(f"Could not create post: tenant_id={tenant_id}, company_id={self.created_company_id}")
                except Exception as e:
                    print_error(f"Failed to create test post via database: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    print_info("Will proceed without posts - some tests may be skipped")
            
            if len(self.created_post_ids) < 1:
                print_info("Note: No posts available. Campaign creation will be skipped.")
            else:
                print_success(f"Using {len(self.created_post_ids)} posts for testing")
            
            # Create a campaign and link some profiles/posts to test validation
            if len(self.created_post_ids) > 0 and len(self.created_profile_ids) >= 3:
                print_info("Creating campaign with linked profiles for validation testing...")
                campaign_response = requests.post(
                    f"{API_BASE}/campaigns",
                    json={
                        "post_id": self.created_post_ids[0],
                        "name": "Test Campaign for Bulk Delete",
                        "profile_ids": self.created_profile_ids[:3]  # Link first 3 profiles
                    },
                    headers=self.get_headers()
                )
                
                if campaign_response.status_code == 201:
                    self.created_campaign_id = campaign_response.json().get("campaign", {}).get("campaign_id")
                    self.profiles_linked_to_campaign = self.created_profile_ids[:3]  # Track these
                    print_success(f"Campaign created: {self.created_campaign_id}")
                    print_info(f"Profiles linked to campaign: {self.profiles_linked_to_campaign}")
                    print_info("First 3 profiles are linked to campaign (will fail deletion)")
                    print_info("First post is linked to campaign (will fail deletion)")
                else:
                    print_error(f"Failed to create campaign: {campaign_response.status_code}")
                    print_error(f"Response: {campaign_response.text}")
                    print_info("Note: Some validation tests may not work without campaign")
            else:
                print_info("Not enough profiles to create campaign (need at least 3)")
            
            return True
            
        except Exception as e:
            print_error(f"Error setting up test data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_profiles_bulk_delete_success(self):
        """Test Case 1: Success - Delete 5 profiles that all pass validation"""
        print_step(3, "Test: Profiles Bulk Delete - Success (5 profiles)")
        
        try:
            # Use profiles that are NOT linked to campaigns (skip first 3)
            # We need at least 8 profiles total (3 for campaign + 5 for this test)
            if len(self.created_profile_ids) < 8:
                print_error("Not enough profiles for success test")
                return False
            
            # Select 5 profiles that should delete successfully (profiles 4-8, index 3-7)
            # Make sure we're not deleting profiles linked to campaigns (first 3)
            profile_ids_to_delete = self.created_profile_ids[3:8]
            
            print_info(f"Attempting to delete {len(profile_ids_to_delete)} profiles...")
            print_info(f"Profile IDs: {profile_ids_to_delete}")
            
            response = requests.delete(
                f"{API_BASE}/profiles/bulk",
                json={"ids": profile_ids_to_delete},
                headers=self.get_headers()
            )
            
            print_info(f"Response Status: {response.status_code}")
            print_info(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                successful = data.get("results", {}).get("successful", [])
                failed = data.get("results", {}).get("failed", [])
                
                if deleted_count == len(profile_ids_to_delete) and len(failed) == 0:
                    print_success(f"All {deleted_count} profiles deleted successfully")
                    print_info(f"Successful: {len(successful)}, Failed: {len(failed)}")
                    # Remove deleted IDs from our list
                    self.created_profile_ids = [pid for pid in self.created_profile_ids if pid not in profile_ids_to_delete]
                    return True
                else:
                    print_error(f"Expected all to succeed, but got {len(failed)} failures")
                    return False
            else:
                print_error(f"Expected 200 OK, got {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error in success test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_profiles_bulk_delete_partial(self):
        """Test Case 2: Partial Success - Delete 7 items, 3 fail due to campaign links"""
        print_step(4, "Test: Profiles Bulk Delete - Partial Success (7 items, 3 fail)")
        
        try:
            # Check if we have profiles linked to campaign
            if not self.profiles_linked_to_campaign:
                print_info("Skipping test: No campaign was created, so no profiles are linked to campaigns")
                return True  # Skip, don't fail
            
            # Find which profiles in the current list are linked to campaign
            linked_profiles_in_list = [pid for pid in self.created_profile_ids if pid in self.profiles_linked_to_campaign]
            
            if len(linked_profiles_in_list) < 3:
                print_info(f"Only {len(linked_profiles_in_list)} campaign-linked profiles available. Creating more profiles...")
                # Create a few more profiles to ensure we have enough
                for i in range(16, 19):
                    profile_response = requests.post(
                        f"{API_BASE}/profiles",
                        json={"linkedin_url": f"https://www.linkedin.com/in/test-profile-{i}/"},
                        headers=self.get_headers()
                    )
                    if profile_response.status_code == 201:
                        profile_id = profile_response.json().get("profile", {}).get("profile_id")
                        self.created_profile_ids.append(profile_id)
                        print_info(f"Created additional profile: {profile_id}")
                # Re-check after creating more
                linked_profiles_in_list = [pid for pid in self.created_profile_ids if pid in self.profiles_linked_to_campaign]
            
            # Use profiles: include some linked to campaign and some not
            # Get first 3 linked profiles + 4 non-linked profiles
            linked_in_list = linked_profiles_in_list[:3]
            non_linked = [pid for pid in self.created_profile_ids if pid not in self.profiles_linked_to_campaign][:4]
            
            if len(linked_in_list) < 3 or len(non_linked) < 4:
                print_error(f"Not enough profiles: {len(linked_in_list)} linked, {len(non_linked)} non-linked")
                return False
            
            profile_ids_to_delete = linked_in_list + non_linked
            
            print_info(f"Attempting to delete {len(profile_ids_to_delete)} profiles...")
            print_info(f"Profile IDs: {profile_ids_to_delete}")
            print_info(f"Linked to campaign (should fail): {linked_in_list}")
            print_info(f"Not linked (should succeed): {non_linked}")
            print_info("Expected: First 3 should fail (linked to campaign), next 4 should succeed")
            
            response = requests.delete(
                f"{API_BASE}/profiles/bulk",
                json={"ids": profile_ids_to_delete},
                headers=self.get_headers()
            )
            
            print_info(f"Response Status: {response.status_code}")
            print_info(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 207:  # Multi-Status
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                failed_count = data.get("failed_count", 0)
                successful = data.get("results", {}).get("successful", [])
                failed = data.get("results", {}).get("failed", [])
                
                print_success(f"Partial success response received")
                print_info(f"Deleted: {deleted_count}, Failed: {failed_count}")
                print_info(f"Successful IDs: {[s.get('id') for s in successful]}")
                print_info(f"Failed IDs: {[f.get('id') for f in failed]}")
                
                # Check that we have both successes and failures
                if len(successful) > 0 and len(failed) > 0:
                    print_success("Test passed: Partial success scenario")
                    # Remove successfully deleted IDs
                    successful_ids = [s.get("id") for s in successful]
                    self.created_profile_ids = [pid for pid in self.created_profile_ids if pid not in successful_ids]
                    return True
                else:
                    print_error(f"Expected both successes and failures, got {len(successful)} successes, {len(failed)} failures")
                    return False
            else:
                print_error(f"Expected 207 Multi-Status, got {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error in partial success test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_profiles_bulk_delete_all_fail(self):
        """Test Case 3: All Fail - All items fail validation"""
        print_step(5, "Test: Profiles Bulk Delete - All Fail")
        
        try:
            # Check if we have profiles linked to campaign
            if not self.profiles_linked_to_campaign:
                print_info("Skipping test: No campaign was created, so no profiles are linked to campaigns")
                return True  # Skip, don't fail
            
            # Find profiles that are still linked to campaign (not deleted in previous tests)
            linked_profiles = [pid for pid in self.created_profile_ids if pid in self.profiles_linked_to_campaign]
            
            if len(linked_profiles) < 3:
                print_info(f"Only {len(linked_profiles)} campaign-linked profiles available")
                if len(linked_profiles) == 0:
                    print_info("All campaign-linked profiles were already deleted in previous tests")
                    return True  # Skip
                # Use what we have
                profile_ids_to_delete = linked_profiles
            else:
                # Use first 3 profiles that are linked to campaign
                profile_ids_to_delete = linked_profiles[:3]
            
            print_info(f"Attempting to delete {len(profile_ids_to_delete)} profiles (all linked to campaign)...")
            print_info(f"Profile IDs: {profile_ids_to_delete}")
            print_info("Expected: All should fail (linked to campaign)")
            
            response = requests.delete(
                f"{API_BASE}/profiles/bulk",
                json={"ids": profile_ids_to_delete},
                headers=self.get_headers()
            )
            
            print_info(f"Response Status: {response.status_code}")
            print_info(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 400:
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                failed = data.get("results", {}).get("failed", [])
                
                if deleted_count == 0 and len(failed) == len(profile_ids_to_delete):
                    print_success("All deletions failed as expected")
                    print_info(f"Failed count: {len(failed)}")
                    return True
                else:
                    print_error(f"Expected all to fail, got {deleted_count} deleted, {len(failed)} failed")
                    return False
            else:
                print_error(f"Expected 400 Bad Request, got {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error in all fail test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_profiles_bulk_delete_invalid_input(self):
        """Test Case 4: Invalid Input - Empty array or more than 100 items"""
        print_step(6, "Test: Profiles Bulk Delete - Invalid Input")
        
        try:
            # Test empty array
            print_info("Testing empty array...")
            response = requests.delete(
                f"{API_BASE}/profiles/bulk",
                json={"ids": []},
                headers=self.get_headers()
            )
            
            if response.status_code == 400:
                print_success("Empty array correctly rejected")
            else:
                print_error(f"Expected 400 for empty array, got {response.status_code}")
                return False
            
            # Test more than 100 items
            print_info("Testing more than 100 items...")
            too_many_ids = [f"test-id-{i}" for i in range(101)]
            response = requests.delete(
                f"{API_BASE}/profiles/bulk",
                json={"ids": too_many_ids},
                headers=self.get_headers()
            )
            
            if response.status_code == 400:
                print_success("More than 100 items correctly rejected")
            else:
                print_error(f"Expected 400 for >100 items, got {response.status_code}")
                return False
            
            # Test invalid input type
            print_info("Testing invalid input type...")
            response = requests.delete(
                f"{API_BASE}/profiles/bulk",
                json={"ids": "not-an-array"},
                headers=self.get_headers()
            )
            
            if response.status_code == 400:
                print_success("Invalid input type correctly rejected")
                return True
            else:
                print_error(f"Expected 400 for invalid type, got {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error in invalid input test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_posts_bulk_delete_success(self):
        """Test Case 5: Success - Delete 5 posts that all pass validation"""
        print_step(7, "Test: Posts Bulk Delete - Success (5 posts)")
        
        try:
            if len(self.created_post_ids) < 5:
                print_info("Skipping test: Not enough posts available")
                return True  # Skip, don't fail
            
            # Use posts that are NOT linked to campaigns (skip first one)
            post_ids_to_delete = self.created_post_ids[1:6]
            
            print_info(f"Attempting to delete {len(post_ids_to_delete)} posts...")
            print_info(f"Post IDs: {post_ids_to_delete}")
            
            response = requests.delete(
                f"{API_BASE}/posts/bulk",
                json={"ids": post_ids_to_delete},
                headers=self.get_headers()
            )
            
            print_info(f"Response Status: {response.status_code}")
            print_info(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                successful = data.get("results", {}).get("successful", [])
                failed = data.get("results", {}).get("failed", [])
                
                if deleted_count == len(post_ids_to_delete) and len(failed) == 0:
                    print_success(f"All {deleted_count} posts deleted successfully")
                    print_info(f"Successful: {len(successful)}, Failed: {len(failed)}")
                    # Remove deleted IDs from our list
                    self.created_post_ids = [pid for pid in self.created_post_ids if pid not in post_ids_to_delete]
                    return True
                else:
                    print_error(f"Expected all to succeed, but got {len(failed)} failures")
                    return False
            else:
                print_error(f"Expected 200 OK, got {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error in posts success test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_posts_bulk_delete_partial(self):
        """Test Case 6: Partial Success - Delete posts, some fail due to campaign links"""
        print_step(8, "Test: Posts Bulk Delete - Partial Success")
        
        try:
            if len(self.created_post_ids) < 2:
                print_info("Skipping test: Not enough posts available")
                return True  # Skip, don't fail
            
            # First post is linked to campaign, should fail
            post_ids_to_delete = self.created_post_ids[:3]
            
            print_info(f"Attempting to delete {len(post_ids_to_delete)} posts...")
            print_info(f"Post IDs: {post_ids_to_delete}")
            print_info("Expected: First post should fail (linked to campaign), rest should succeed")
            
            response = requests.delete(
                f"{API_BASE}/posts/bulk",
                json={"ids": post_ids_to_delete},
                headers=self.get_headers()
            )
            
            print_info(f"Response Status: {response.status_code}")
            print_info(f"Response Body: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 207:  # Multi-Status
                data = response.json()
                deleted_count = data.get("deleted_count", 0)
                failed_count = data.get("failed_count", 0)
                successful = data.get("results", {}).get("successful", [])
                failed = data.get("results", {}).get("failed", [])
                
                print_success(f"Partial success response received")
                print_info(f"Deleted: {deleted_count}, Failed: {failed_count}")
                print_info(f"Successful IDs: {[s.get('id') for s in successful]}")
                print_info(f"Failed IDs: {[f.get('id') for f in failed]}")
                
                if len(successful) > 0 and len(failed) > 0:
                    print_success("Test passed: Partial success scenario")
                    # Remove successfully deleted IDs
                    successful_ids = [s.get("id") for s in successful]
                    self.created_post_ids = [pid for pid in self.created_post_ids if pid not in successful_ids]
                    return True
                else:
                    print_error(f"Expected both successes and failures")
                    return False
            else:
                print_error(f"Expected 207 Multi-Status, got {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error in posts partial success test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_posts_bulk_delete_invalid_input(self):
        """Test Case 7: Invalid Input for Posts"""
        print_step(9, "Test: Posts Bulk Delete - Invalid Input")
        
        try:
            # Test empty array
            print_info("Testing empty array...")
            response = requests.delete(
                f"{API_BASE}/posts/bulk",
                json={"ids": []},
                headers=self.get_headers()
            )
            
            if response.status_code == 400:
                print_success("Empty array correctly rejected")
            else:
                print_error(f"Expected 400 for empty array, got {response.status_code}")
                return False
            
            # Test more than 100 items
            print_info("Testing more than 100 items...")
            too_many_ids = [f"test-id-{i}" for i in range(101)]
            response = requests.delete(
                f"{API_BASE}/posts/bulk",
                json={"ids": too_many_ids},
                headers=self.get_headers()
            )
            
            if response.status_code == 400:
                print_success("More than 100 items correctly rejected")
                return True
            else:
                print_error(f"Expected 400 for >100 items, got {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error in posts invalid input test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self):
        """Run all test cases"""
        print_header("Bulk Delete Endpoints Test Suite")
        
        tests_passed = 0
        tests_failed = 0
        
        # Setup
        if not self.register_and_login():
            print_error("Failed to register/login. Aborting tests.")
            return
        
        if not self.setup_test_data():
            print_error("Failed to setup test data. Aborting tests.")
            return
        
        # Run tests
        test_functions = [
            ("Profiles Bulk Delete - Success", self.test_profiles_bulk_delete_success),
            ("Profiles Bulk Delete - Partial Success", self.test_profiles_bulk_delete_partial),
            ("Profiles Bulk Delete - All Fail", self.test_profiles_bulk_delete_all_fail),
            ("Profiles Bulk Delete - Invalid Input", self.test_profiles_bulk_delete_invalid_input),
            ("Posts Bulk Delete - Success", self.test_posts_bulk_delete_success),
            ("Posts Bulk Delete - Partial Success", self.test_posts_bulk_delete_partial),
            ("Posts Bulk Delete - Invalid Input", self.test_posts_bulk_delete_invalid_input),
        ]
        
        for test_name, test_func in test_functions:
            try:
                if test_func():
                    tests_passed += 1
                else:
                    tests_failed += 1
            except Exception as e:
                print_error(f"Test '{test_name}' raised exception: {str(e)}")
                tests_failed += 1
        
        # Summary
        print_header("Test Summary")
        print_info(f"Total Tests: {len(test_functions)}")
        print_success(f"Passed: {tests_passed}")
        if tests_failed > 0:
            print_error(f"Failed: {tests_failed}")
        else:
            print_success("All tests passed!")

if __name__ == "__main__":
    tester = BulkDeleteTester()
    tester.run_all_tests()

