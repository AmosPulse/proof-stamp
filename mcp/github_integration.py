"""
GitHub Integration Module for AI Factory
Automatically creates Issues from BACKLOG.yml and manages Project board
"""

import os
import yaml
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
from datetime import datetime

@dataclass
class GitHubConfig:
    token: str
    repo_owner: str
    repo_name: str
    project_id: Optional[str] = None

class GitHubIntegration:
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Factory-Orchestrator"
        }
        
    async def create_issue_from_task(self, task: Dict[str, Any], epic_title: str) -> Optional[str]:
        """Create a GitHub Issue from a backlog task"""
        try:
            issue_data = {
                "title": f"[{epic_title}] {task['task']}",
                "body": self._format_issue_body(task, epic_title),
                "labels": [
                    "ai-factory",
                    f"epic:{epic_title.lower().replace(' ', '-')}",
                    f"priority:{task.get('priority', 'medium')}",
                    f"estimate:{task.get('estimate', 'unknown')}"
                ]
            }
            
            url = f"{self.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=issue_data) as response:
                    if response.status == 201:
                        issue = await response.json()
                        print(f"[OK] Created GitHub Issue #{issue['number']}: {task['task']}")
                        return str(issue['number'])
                    else:
                        error_text = await response.text()
                        print(f"[ERROR] Failed to create issue: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"[ERROR] Error creating GitHub issue: {e}")
            return None
    
    def _format_issue_body(self, task: Dict[str, Any], epic_title: str) -> str:
        """Format the issue body with task details"""
        body = f"""## Task Details

**Epic:** {epic_title}
**Estimate:** {task.get('estimate', 'Not specified')}
**Cost Category:** {task.get('cost_category', 'Not specified')}

### Description
{task['task']}

### Dependencies
"""
        
        dependencies = task.get('dependencies', [])
        if dependencies:
            for dep in dependencies:
                body += f"- {dep}\n"
        else:
            body += "- None\n"
            
        body += f"""
### Acceptance Criteria
- [ ] Task implementation completed
- [ ] Code reviewed and approved
- [ ] Tests passing
- [ ] Documentation updated if needed

---
*This issue was automatically created by the AI Factory Orchestrator*
*Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return body

    async def add_issue_to_project(self, issue_number: str) -> bool:
        """Add an issue to the GitHub Project board"""
        if not self.config.project_id:
            print("[WARNING] No project ID configured, skipping project board update")
            return False
            
        try:
            # GitHub Projects v2 API requires GraphQL
            query = """
            mutation($projectId: ID!, $contentId: ID!) {
                addProjectV2ItemById(input: {
                    projectId: $projectId
                    contentId: $contentId
                }) {
                    item {
                        id
                    }
                }
            }
            """
            
            # First get the issue's node ID
            issue_url = f"{self.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{issue_number}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(issue_url, headers=self.headers) as response:
                    if response.status == 200:
                        issue_data = await response.json()
                        content_id = issue_data['node_id']
                        
                        # Add to project using GraphQL
                        graphql_headers = {
                            **self.headers,
                            "Accept": "application/vnd.github.v4+json"
                        }
                        
                        variables = {
                            "projectId": self.config.project_id,
                            "contentId": content_id
                        }
                        
                        graphql_data = {
                            "query": query,
                            "variables": variables
                        }
                        
                        async with session.post(
                            "https://api.github.com/graphql",
                            headers=graphql_headers,
                            json=graphql_data
                        ) as gql_response:
                            if gql_response.status == 200:
                                result = await gql_response.json()
                                if 'errors' not in result:
                                    print(f"[OK] Added issue #{issue_number} to project board")
                                    return True
                                else:
                                    print(f"[ERROR] GraphQL errors: {result['errors']}")
                                    return False
                            else:
                                error_text = await gql_response.text()
                                print(f"[ERROR] Failed to add to project: {gql_response.status} - {error_text}")
                                return False
                    else:
                        print(f"[ERROR] Failed to get issue details: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"[ERROR] Error adding issue to project: {e}")
            return False

    async def dispatch_backlog(self, backlog_path: str = "product/BACKLOG.yml") -> Dict[str, List[str]]:
        """Main dispatch function: reads backlog and creates GitHub Issues"""
        try:
            # Read the backlog file
            with open(backlog_path, 'r', encoding='utf-8') as file:
                backlog_data = yaml.safe_load(file)
            
            if not backlog_data or 'backlog' not in backlog_data:
                print("[ERROR] No backlog data found in BACKLOG.yml")
                return {}
            
            created_issues = {}
            
            # Process each epic
            for epic_key, epic_data in backlog_data['backlog'].items():
                epic_title = epic_data.get('title', epic_key)
                tasks = epic_data.get('tasks', [])
                
                print(f"\n[PROCESSING] Epic: {epic_title}")
                print(f"   Tasks to create: {len(tasks)}")
                
                epic_issues = []
                
                # Create issues for each task
                for task in tasks:
                    issue_number = await self.create_issue_from_task(task, epic_title)
                    if issue_number:
                        epic_issues.append(issue_number)
                        
                        # Add to project board if configured
                        if self.config.project_id:
                            await self.add_issue_to_project(issue_number)
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.5)
                
                created_issues[epic_key] = epic_issues
                print(f"[OK] Created {len(epic_issues)} issues for epic: {epic_title}")
            
            # Summary
            total_issues = sum(len(issues) for issues in created_issues.values())
            print(f"\n[SUCCESS] Dispatch complete! Created {total_issues} GitHub Issues across {len(created_issues)} epics")
            
            return created_issues
            
        except FileNotFoundError:
            print(f"[ERROR] Backlog file not found: {backlog_path}")
            return {}
        except yaml.YAMLError as e:
            print(f"[ERROR] Error parsing BACKLOG.yml: {e}")
            return {}
        except Exception as e:
            print(f"[ERROR] Error during dispatch: {e}")
            return {}

def load_github_config() -> Optional[GitHubConfig]:
    """Load GitHub configuration from environment variables"""
    token = os.getenv('REPO_TOKEN')
    repo_owner = os.getenv('GITHUB_REPO_OWNER', 'AmosPulse')
    repo_name = os.getenv('GITHUB_REPO_NAME', 'proof-stamp')
    project_id = os.getenv('PROJECT_ID')  # Optional
    
    if not token:
        print("[ERROR] REPO_TOKEN environment variable not set")
        return None
    
    return GitHubConfig(
        token=token,
        repo_owner=repo_owner,
        repo_name=repo_name,
        project_id=project_id
    )

async def main():
    """Main entry point for testing"""
    config = load_github_config()
    if not config:
        return
    
    github = GitHubIntegration(config)
    await github.dispatch_backlog()

if __name__ == "__main__":
    asyncio.run(main())
