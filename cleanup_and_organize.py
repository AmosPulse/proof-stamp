#!/usr/bin/env python3
"""
Cleanup duplicate issues and organize the remaining ones with proper status management
"""

import asyncio
import sys
from pathlib import Path
import re

# Add the mcp directory to the path
sys.path.append(str(Path(__file__).parent / "mcp"))

from github_integration import GitHubIntegration, load_github_config

class IssueOrganizer:
    def __init__(self, github_integration: GitHubIntegration):
        self.github = github_integration
        
    async def get_all_open_issues(self):
        """Get all open issues from the repository"""
        try:
            url = f"{self.github.base_url}/repos/{self.github.config.repo_owner}/{self.github.config.repo_name}/issues"
            params = {"state": "open", "per_page": 100}
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.github.headers, params=params) as response:
                    if response.status == 200:
                        issues = await response.json()
                        return issues
                    else:
                        print(f"[ERROR] Failed to get issues: {response.status}")
                        return []
        except Exception as e:
            print(f"[ERROR] Error getting issues: {e}")
            return []
    
    async def close_duplicate_issues(self, issues):
        """Close duplicate issues, keeping only the original ones (#109-126)"""
        original_range = range(109, 127)  # Original issues #109-#126
        duplicates_closed = 0
        
        for issue in issues:
            issue_number = issue['number']
            
            # Close duplicates (anything above #126 that matches our patterns)
            if (issue_number not in original_range and 
                'ai-factory' in [label['name'] for label in issue.get('labels', [])]):
                
                try:
                    # Close the duplicate issue
                    url = f"{self.github.base_url}/repos/{self.github.config.repo_owner}/{self.github.config.repo_name}/issues/{issue_number}"
                    data = {
                        "state": "closed",
                        "state_reason": "not_planned"
                    }
                    
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.patch(url, headers=self.github.headers, json=data) as response:
                            if response.status == 200:
                                print(f"[OK] Closed duplicate issue #{issue_number}")
                                duplicates_closed += 1
                                
                                # Add closing comment
                                comment_url = f"{url}/comments"
                                comment_data = {
                                    "body": "🔄 **Closed as duplicate** - This issue was automatically created multiple times. The original issue in the #109-#126 range will be used instead."
                                }
                                await session.post(comment_url, headers=self.github.headers, json=comment_data)
                                
                            else:
                                print(f"[ERROR] Failed to close issue #{issue_number}: {response.status}")
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"[ERROR] Error closing issue #{issue_number}: {e}")
        
        return duplicates_closed
    
    async def organize_original_issues(self):
        """Organize the original 18 issues (#109-#126) with proper assignments and status"""
        
        # Original issue mapping with agent assignments
        issue_mappings = {
            109: {"task": "Database schema design and migrations", "epic": "Core Infrastructure Setup", "agent": "architect", "priority": "critical"},
            110: {"task": "MCP server configuration and testing", "epic": "Core Infrastructure Setup", "agent": "qa-bot", "priority": "high"},
            111: {"task": "Email notification service integration", "epic": "Core Infrastructure Setup", "agent": "notification-agent", "priority": "high"},
            112: {"task": "Task dependency resolution engine", "epic": "Orchestrator Core Features", "agent": "architect", "priority": "critical"},
            113: {"task": "Priority-based scheduling algorithm", "epic": "Orchestrator Core Features", "agent": "architect", "priority": "high"},
            114: {"task": "Resource allocation and limiting", "epic": "Orchestrator Core Features", "agent": "architect", "priority": "high"},
            115: {"task": "Stuck-guard timeout detection", "epic": "Monitoring & Cost Control", "agent": "stuck-guard", "priority": "critical"},
            116: {"task": "Cost-governor budget enforcement", "epic": "Monitoring & Cost Control", "agent": "cost-governor", "priority": "high"},
            117: {"task": "Real-time dashboard for agent status", "epic": "Monitoring & Cost Control", "agent": "dashboard-smith", "priority": "medium"},
            118: {"task": "GitHub Actions workflow enhancement", "epic": "CI/CD Pipeline Integration", "agent": "release-bot", "priority": "high"},
            119: {"task": "Project board automation", "epic": "CI/CD Pipeline Integration", "agent": "release-bot", "priority": "medium"},
            120: {"task": "Deployment pipeline orchestration", "epic": "CI/CD Pipeline Integration", "agent": "release-bot", "priority": "medium"},
            121: {"task": "Migration orchestration system", "epic": "Database Management Workflows", "agent": "architect", "priority": "low"},
            122: {"task": "Backup and restore automation", "epic": "Database Management Workflows", "agent": "architect", "priority": "low"},
            123: {"task": "Performance monitoring integration", "epic": "Database Management Workflows", "agent": "architect", "priority": "low"},
            124: {"task": "Multi-channel notification routing", "epic": "Advanced Notification System", "agent": "notification-agent", "priority": "low"},
            125: {"task": "Alert severity and escalation rules", "epic": "Advanced Notification System", "agent": "notification-agent", "priority": "low"},
            126: {"task": "Notification template management", "epic": "Advanced Notification System", "agent": "notification-agent", "priority": "low"},
        }
        
        organized_count = 0
        
        for issue_number, info in issue_mappings.items():
            try:
                # Add agent assignment comment
                await self.github._assign_issue_to_agent(str(issue_number), info["agent"])
                
                # Set initial status based on priority
                if info["priority"] == "critical":
                    status = "in_progress"  # Start critical tasks immediately
                elif info["priority"] == "high":
                    status = "to_do"  # High priority ready to start
                else:
                    status = "to_do"  # Medium/low priority in backlog
                
                await self.github.update_issue_status(str(issue_number), status, info["agent"])
                
                organized_count += 1
                print(f"[OK] Organized issue #{issue_number}: {info['task'][:50]}... -> {info['agent']} ({status})")
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"[ERROR] Failed to organize issue #{issue_number}: {e}")
        
        return organized_count

async def main():
    """Main cleanup and organization function"""
    print("🧹 CLEANUP AND ORGANIZATION SYSTEM")
    print("=" * 50)
    
    # Load GitHub configuration
    config = load_github_config()
    if not config:
        print("[ERROR] GitHub configuration not found")
        return False
    
    github = GitHubIntegration(config)
    organizer = IssueOrganizer(github)
    
    # Get all open issues
    print("[1/3] Getting all open issues...")
    issues = await organizer.get_all_open_issues()
    print(f"Found {len(issues)} open issues")
    
    # Close duplicates
    print("\n[2/3] Closing duplicate issues...")
    duplicates_closed = await organizer.close_duplicate_issues(issues)
    print(f"Closed {duplicates_closed} duplicate issues")
    
    # Organize original issues
    print("\n[3/3] Organizing original issues with proper assignments and status...")
    organized_count = await organizer.organize_original_issues()
    print(f"Organized {organized_count} original issues")
    
    print("\n" + "=" * 50)
    print("✅ CLEANUP COMPLETE!")
    print(f"- Closed {duplicates_closed} duplicate issues")
    print(f"- Organized {organized_count} original issues")
    print("- Issues #109-#126 now have proper agent assignments and status")
    print("- Critical issues moved to 'In Progress'")
    print("- High priority issues ready in 'To Do'")
    print("\nCheck your GitHub project board!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)