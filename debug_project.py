#!/usr/bin/env python3
"""
Debug GitHub Project configuration - check what fields and options are available
"""

import asyncio
import sys
from pathlib import Path

# Add the mcp directory to the path
sys.path.append(str(Path(__file__).parent / "mcp"))

from github_integration import GitHubIntegration, load_github_config

async def debug_project():
    """Debug project configuration to understand available fields and options"""
    print("GITHUB PROJECT DEBUG")
    print("=" * 50)
    
    # Load GitHub configuration
    config = load_github_config()
    if not config:
        print("[ERROR] GitHub configuration not found")
        print("Environment variables needed:")
        print("  - REPO_TOKEN: GitHub token")
        print("  - REPO_OWNER: Repository owner (default: AmosPulse)")
        print("  - REPO_NAME: Repository name (default: proof-stamp)")
        print("  - PROJECT_ID: GitHub Project ID")
        return False
    
    if not config.project_id:
        print("[ERROR] PROJECT_ID not set - cannot debug project")
        return False
    
    print(f"Repository: {config.repo_owner}/{config.repo_name}")
    print(f"Project ID: {config.project_id}")
    print()
    
    github = GitHubIntegration(config)
    
    # Test with a known issue
    test_issue = "109"  # Using issue #109 as test
    
    print(f"Testing with issue #{test_issue}")
    success = await github._update_project_status_field(test_issue, "To Do")
    
    if success:
        print("\n[SUCCESS] Project status field update worked!")
    else:
        print("\n[FAILED] Project status field update failed - check debug output above")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(debug_project())
    sys.exit(0 if success else 1)