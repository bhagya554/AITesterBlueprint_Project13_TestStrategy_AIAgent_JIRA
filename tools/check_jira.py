#!/usr/bin/env python3
"""
JIRA Connectivity Check Tool
Tests connection to JIRA Cloud REST API v3
Usage: python tools/check_jira.py
"""

import os
import sys
import base64
import httpx
from dotenv import load_dotenv

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def check_jira_connection():
    """Test JIRA API connection and return detailed status."""
    
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip('/')
    email = os.getenv("JIRA_EMAIL", "")
    api_token = os.getenv("JIRA_API_TOKEN", "")
    
    # Validation checks
    errors = []
    if not base_url:
        errors.append("❌ JIRA_BASE_URL not set in .env")
    if not email:
        errors.append("❌ JIRA_EMAIL not set in .env")
    if not api_token:
        errors.append("❌ JIRA_API_TOKEN not set in .env")
    
    if errors:
        print("\n".join(errors))
        print("\nℹ️  Get your JIRA API token from: https://id.atlassian.com/manage-profile/security/api-tokens")
        return False
    
    # Build auth header
    auth_string = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Test connection to /myself endpoint
    url = f"{base_url}/rest/api/3/myself"
    
    print(f"🔍 Testing JIRA connection to: {base_url}")
    print(f"   Email: {email}")
    
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            display_name = data.get("displayName", "Unknown")
            account_id = data.get("accountId", "Unknown")
            print(f"\n✅ JIRA connection successful!")
            print(f"   User: {display_name}")
            print(f"   Account ID: {account_id}")
            return True
            
        elif response.status_code == 401:
            print(f"\n❌ JIRA authentication failed (401)")
            print(f"   Check your email and API token in .env")
            print(f"   Response: {response.text[:200]}")
            return False
            
        elif response.status_code == 403:
            print(f"\n❌ JIRA access forbidden (403)")
            print(f"   Your account may not have API access")
            print(f"   Response: {response.text[:200]}")
            return False
            
        elif response.status_code == 404:
            print(f"\n❌ JIRA URL not found (404)")
            print(f"   Check JIRA_BASE_URL in .env")
            print(f"   Expected format: https://your-domain.atlassian.net")
            return False
            
        else:
            print(f"\n❌ JIRA connection failed (HTTP {response.status_code})")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except httpx.ConnectError as e:
        print(f"\n❌ Cannot connect to JIRA server")
        print(f"   Error: {e}")
        print(f"   Check your internet connection and JIRA_BASE_URL")
        return False
        
    except httpx.TimeoutException:
        print(f"\n❌ JIRA connection timed out")
        print(f"   Server may be down or unreachable")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        return False


def test_ticket_fetch():
    """Test fetching a sample ticket if connection works."""
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip('/')
    email = os.getenv("JIRA_EMAIL", "")
    api_token = os.getenv("JIRA_API_TOKEN", "")
    
    auth_string = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Try to get any issue from the project
    url = f"{base_url}/rest/api/3/search?jql=order+by+created+DESC&maxResults=1"
    
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            issues = data.get("issues", [])
            if issues:
                key = issues[0].get("key")
                summary = issues[0].get("fields", {}).get("summary", "No summary")
                print(f"\n📋 Sample ticket access:")
                print(f"   Found: {key} - {summary}")
                return True
            else:
                print(f"\n⚠️  No tickets found (empty project or no access)")
                return True
    except Exception as e:
        print(f"\n⚠️  Could not fetch sample ticket: {e}")
        return False
    
    return False


if __name__ == "__main__":
    print("=" * 50)
    print("JIRA Connectivity Check Tool")
    print("=" * 50)
    
    success = check_jira_connection()
    
    if success:
        test_ticket_fetch()
        print("\n✅ All JIRA checks passed!")
        sys.exit(0)
    else:
        print("\n❌ JIRA checks failed. Please fix the issues above.")
        sys.exit(1)
