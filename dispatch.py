#!/usr/bin/env python3
"""
AI Factory Dispatch Script
Automatically creates GitHub Issues from BACKLOG.yml and updates Project board
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the mcp directory to the path
sys.path.append(str(Path(__file__).parent / "mcp"))

from github_integration import GitHubIntegration, load_github_config

async def dispatch():
    """Main dispatch function"""
    print("[AI Factory] Dispatch Starting...")
    print("=" * 50)
    
    # Load GitHub configuration
    config = load_github_config()
    if not config:
        print("X GitHub configuration not found. Please set up environment variables:")
        print("   - REPO_TOKEN: Your GitHub personal access token")
        print("   - REPO_OWNER: Repository owner (default: AmosPulse)")
        print("   - REPO_NAME: Repository name (default: proof-stamp)")
        print("   - PROJECT_ID: Project board ID (optional)")
        return False
    
    print(f"[OK] GitHub config loaded:")
    print(f"   Repository: {config.repo_owner}/{config.repo_name}")
    print(f"   Project ID: {config.project_id or 'Not configured'}")
    print()
    
    # Initialize GitHub integration
    github = GitHubIntegration(config)
    
    # Dispatch the backlog
    created_issues = await github.dispatch_backlog()
    
    if created_issues:
        print("\n" + "=" * 50)
        print("[SUCCESS] Dispatch Summary:")
        for epic_key, issue_numbers in created_issues.items():
            print(f"   {epic_key}: {len(issue_numbers)} issues created")
        
        total_issues = sum(len(issues) for issues in created_issues.values())
        print(f"\nTotal: {total_issues} GitHub Issues created")
        print("\n[SUCCESS] AI Factory dispatch completed successfully!")
        print("[INFO] Check your GitHub repository and project board for the new issues.")
        return True
    else:
        print("\n[ERROR] No issues were created. Check the logs above for errors.")
        return False

if __name__ == "__main__":
    success = asyncio.run(dispatch())
    sys.exit(0 if success else 1)
