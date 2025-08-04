#!/usr/bin/env python3
"""
Reset all issues to "To Do" status using labels
"""

import asyncio
import sys
from pathlib import Path

# Add the mcp directory to the path
sys.path.append(str(Path(__file__).parent / "mcp"))

from github_integration import GitHubIntegration, load_github_config

async def reset_all_issues_to_todo():
    """Reset all issues #109-#126 to 'To Do' status"""
    print("RESET ALL ISSUES TO 'TO DO' STATUS")
    print("=" * 50)
    
    # Load GitHub configuration
    config = load_github_config()
    if not config:
        print("[ERROR] GitHub configuration not found")
        return False
    
    github = GitHubIntegration(config)
    
    # Original 18 issues
    issue_numbers = list(range(109, 127))  # #109-#126
    
    print(f"Resetting {len(issue_numbers)} issues to 'To Do' status...")
    
    success_count = 0
    
    for issue_number in issue_numbers:
        try:
            success = await github.update_issue_status(str(issue_number), "to_do")
            if success:
                success_count += 1
                print(f"[OK] Reset issue #{issue_number} to 'To Do'")
            else:
                print(f"[ERROR] Failed to reset issue #{issue_number}")
            
            # Rate limiting
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"[ERROR] Error resetting issue #{issue_number}: {e}")
    
    print("\n" + "=" * 50)
    print(f"RESET COMPLETE: {success_count}/{len(issue_numbers)} issues reset to 'To Do'")
    print("All issues now have 'status:to-do' label and status comment")
    
    return success_count == len(issue_numbers)

if __name__ == "__main__":
    success = asyncio.run(reset_all_issues_to_todo())
    sys.exit(0 if success else 1)