#!/usr/bin/env python3
"""
Test script for GET /api/profiles endpoint
Tests pagination, filtering, search, sorting, and stats
"""

import requests
import json
import sys
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:5000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "TestPass123"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_response(response: requests.Response, description: str = ""):
    """Print formatted response."""
    print(f"\n{description}")
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(f"Response Text: {response.text}")

def authenticate() -> Optional[str]:
    """Authenticate and return JWT token."""
    print_section("Authentication")
    
    # Try to login first
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    print(f"Attempting to login with {TEST_EMAIL}...")
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("[OK] Login successful")
        return token
    
    # If login fails, try to register
    print("Login failed, attempting to register...")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "first_name": "Test",
        "last_name": "User",
        "company_name": "Test Company"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    
    if response.status_code == 201:
        token = response.json().get("access_token")
        print("[OK] Registration successful")
        return token
    elif response.status_code == 400 and "already registered" in response.text.lower():
        print("User already exists, but login failed. Please check credentials.")
        print(f"Response: {response.text}")
        return None
    else:
        print(f"[ERROR] Registration failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def test_list_profiles(token: str, params: Dict[str, Any] = None, description: str = ""):
    """Test GET /api/profiles endpoint with given parameters."""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/profiles"
    
    if params:
        # Build query string
        query_params = []
        for key, value in params.items():
            if value is not None:
                query_params.append(f"{key}={value}")
        if query_params:
            url += "?" + "&".join(query_params)
    
    print(f"\nRequest: GET {url}")
    response = requests.get(url, headers=headers)
    
    print_response(response, description or f"GET /api/profiles with params: {params}")
    
    if response.status_code == 200:
        data = response.json()
        profiles = data.get("profiles", [])
        pagination = data.get("pagination", {})
        stats = data.get("stats", {})
        
        print(f"\n[SUCCESS]")
        print(f"  Profiles returned: {len(profiles)}")
        print(f"  Pagination: Page {pagination.get('page')}/{pagination.get('pages')} "
              f"(Total: {pagination.get('total')}, Limit: {pagination.get('limit')})")
        print(f"  Stats: Total={stats.get('total')}, Scraped={stats.get('scraped')}, "
              f"Pending={stats.get('pending')}, Failed={stats.get('failed')}")
        
        if profiles:
            print(f"\n  First profile preview:")
            first = profiles[0]
            print(f"    - ID: {first.get('profile_id')}")
            print(f"    - Name: {first.get('person_name')}")
            print(f"    - Status: {first.get('status')}")
            print(f"    - Company: {first.get('company')}")
            print(f"    - Location: {first.get('location')}")
    
    return response

def main():
    """Run all tests."""
    print_section("Testing GET /api/profiles Endpoint")
    
    # Authenticate
    token = authenticate()
    if not token:
        print("\n[ERROR] Authentication failed. Cannot proceed with tests.")
        sys.exit(1)
    
    # Test 1: Basic list (no parameters)
    print_section("Test 1: Basic List (Default)")
    test_list_profiles(token, description="Get all profiles with default pagination")
    
    # Test 2: Pagination
    print_section("Test 2: Pagination")
    test_list_profiles(token, {"page": 1, "limit": 5}, "Get first 5 profiles")
    test_list_profiles(token, {"page": 2, "limit": 5}, "Get next 5 profiles")
    
    # Test 3: Filtering by status
    print_section("Test 3: Filtering by Status")
    test_list_profiles(token, {"status": "scraped"}, "Filter by status=scraped")
    test_list_profiles(token, {"status": "url_only"}, "Filter by status=url_only")
    test_list_profiles(token, {"status": "scraping_failed"}, "Filter by status=scraping_failed")
    
    # Test 4: Filtering by company
    print_section("Test 4: Filtering by Company")
    test_list_profiles(token, {"company": "Tech"}, "Filter by company containing 'Tech'")
    
    # Test 5: Filtering by location
    print_section("Test 5: Filtering by Location")
    test_list_profiles(token, {"location": "San"}, "Filter by location containing 'San'")
    
    # Test 6: Filtering by industry
    print_section("Test 6: Filtering by Industry")
    test_list_profiles(token, {"industry": "Technology"}, "Filter by industry containing 'Technology'")
    
    # Test 7: Search
    print_section("Test 7: Search")
    test_list_profiles(token, {"search": "John"}, "Search for 'John' in name, headline, company")
    
    # Test 8: Sorting
    print_section("Test 8: Sorting")
    test_list_profiles(token, {"sort": "person_name", "order": "asc"}, "Sort by person_name ascending")
    test_list_profiles(token, {"sort": "created_at", "order": "desc"}, "Sort by created_at descending (default)")
    test_list_profiles(token, {"sort": "scraped_at", "order": "desc"}, "Sort by scraped_at descending")
    
    # Test 9: Combined filters
    print_section("Test 9: Combined Filters")
    test_list_profiles(
        token,
        {"status": "scraped", "company": "Tech", "page": 1, "limit": 10},
        "Combined: status=scraped, company=Tech, page=1, limit=10"
    )
    
    # Test 10: Invalid parameters (should default gracefully)
    print_section("Test 10: Invalid Parameters (Error Handling)")
    test_list_profiles(token, {"page": -1, "limit": 200}, "Invalid page and limit (should default)")
    test_list_profiles(token, {"sort": "invalid_field", "order": "invalid"}, "Invalid sort field and order (should default)")
    
    # Test 11: Empty results
    print_section("Test 11: Empty Results")
    test_list_profiles(token, {"status": "nonexistent_status"}, "Filter by nonexistent status (should return empty)")
    
    print_section("All Tests Completed")
    print("\n[OK] Test script finished successfully!")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to the server.")
        print(f"  Make sure the Flask server is running on {BASE_URL}")
        print(f"  Start it with: python run.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

