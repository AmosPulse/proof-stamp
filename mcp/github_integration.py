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

    def _assign_agent_to_task(self, task: Dict[str, Any], epic_title: str) -> Optional[str]:
        """Auto-assign agent based on task content and epic type"""
        task_text = task['task'].lower()
        epic_lower = epic_title.lower()
        
        # Database/Storage tasks
        if any(word in task_text for word in ['database', 'schema', 'migration', 'backup', 'restore']):
            return 'architect'  # Database architecture decisions
        
        # Monitoring/Observability tasks  
        if any(word in task_text for word in ['stuck-guard', 'timeout', 'monitoring', 'dashboard']):
            if 'dashboard' in task_text:
                return 'dashboard-smith'  # UI/Dashboard work
            return 'stuck-guard'  # Monitoring logic
        
        # Cost/Budget tasks
        if any(word in task_text for word in ['cost', 'budget', 'governor']):
            return 'cost-governor'  # Assuming we have this agent
        
        # CI/CD and Deployment tasks
        if any(word in task_text for word in ['github', 'workflow', 'deployment', 'pipeline', 'project board']):
            return 'release-bot'  # Handles deployments and CI/CD
        
        # Notification/Communication tasks
        if any(word in task_text for word in ['notification', 'email', 'alert', 'routing']):
            return 'notification-agent'  # Assuming we have this
        
        # Web/Extension tasks
        if any(word in task_text for word in ['extension', 'browser', 'web', 'scraping']):
            return 'extension-builder'  # Web-related work
            
        # Crawling/Data extraction
        if any(word in task_text for word in ['crawler', 'crawling', 'scraping', 'extraction']):
            return 'crawler-bot'  # Data gathering
        
        # Watermarking/Content tasks
        if any(word in task_text for word in ['watermark', 'content', 'proof', 'stamp']):
            return 'watermark-guru'  # Content processing
            
        # Similarity/ML tasks  
        if any(word in task_text for word in ['similarity', 'detection', 'duplicate', 'ml', 'model']):
            return 'similarity-brain'  # AI/ML work
        
        # Testing/QA tasks
        if any(word in task_text for word in ['test', 'testing', 'validation', 'qa', 'quality']):
            return 'qa-bot'  # Quality assurance
            
        # Core orchestration tasks
        if any(word in task_text for word in ['orchestrator', 'dependency', 'scheduling', 'resource']):
            return 'architect'  # System architecture
            
        # Default to architect for system-level tasks
        return 'architect'

    async def _assign_issue_to_agent(self, issue_number: str, agent_name: str) -> bool:
        """Assign a GitHub issue to an agent (as assignee)"""
        try:
            # In GitHub, we'll use the agent name as the assignee
            # For now, we'll add a comment indicating the assigned agent
            url = f"{self.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{issue_number}/comments"
            
            comment_data = {
                "body": f"🤖 **Auto-assigned to agent:** `{agent_name}`\n\nThis issue has been automatically assigned based on the task content and agent expertise."
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=comment_data) as response:
                    if response.status == 201:
                        print(f"[OK] Assigned issue #{issue_number} to agent: {agent_name}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"[ERROR] Failed to assign issue: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            print(f"[ERROR] Error assigning issue to agent: {e}")
            return False

    async def _move_issue_to_column(self, issue_number: str, column_name: str) -> bool:
        """Move an issue to a specific project board column"""
        try:
            if not self.config.project_id:
                print("[WARNING] No project ID configured, cannot move issue to column")
                return False
                
            # First, get the project columns
            columns_url = f"https://api.github.com/projects/columns?project_id={self.config.project_id}"
            
            async with aiohttp.ClientSession() as session:
                # Get project columns
                async with session.get(columns_url, headers=self.headers) as response:
                    if response.status != 200:
                        print(f"[ERROR] Failed to get project columns: {response.status}")
                        return False
                    
                    columns = await response.json()
                    target_column = None
                    
                    for column in columns:
                        if column['name'].lower() == column_name.lower():
                            target_column = column
                            break
                    
                    if not target_column:
                        print(f"[ERROR] Column '{column_name}' not found in project")
                        return False
                
                # Get the issue's current project card (if any)
                issue_url = f"{self.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{issue_number}"
                async with session.get(issue_url, headers=self.headers) as response:
                    if response.status != 200:
                        print(f"[ERROR] Failed to get issue: {response.status}")
                        return False
                    
                    issue_data = await response.json()
                    issue_node_id = issue_data['node_id']
                
                # Move the card to the target column
                cards_url = f"https://api.github.com/projects/columns/{target_column['id']}/cards"
                card_data = {
                    "content_id": issue_data['id'],
                    "content_type": "Issue"
                }
                
                async with session.post(cards_url, headers=self.headers, json=card_data) as response:
                    if response.status == 201:
                        print(f"[OK] Moved issue #{issue_number} to '{column_name}' column")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"[ERROR] Failed to move issue to column: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            print(f"[ERROR] Error moving issue to column: {e}")
            return False

    async def update_issue_status(self, issue_number: str, status: str, agent_name: str = None) -> bool:
        """Update issue status and move to appropriate project board column"""
        try:
            status_mapping = {
                "to_do": "To Do",
                "in_progress": "In Progress", 
                "review": "Review",
                "done": "Done"
            }
            
            column_name = status_mapping.get(status.lower(), "To Do")
            
            # Move to appropriate column
            moved = await self._move_issue_to_column(issue_number, column_name)
            
            # Add status comment
            comment_body = f"🔄 **Status Update:** {column_name}"
            if agent_name:
                comment_body += f" (by {agent_name})"
            
            # Add status-specific information
            if status.lower() == "in_progress":
                comment_body += "\n\n✅ Work has begun on this task."
            elif status.lower() == "review":
                comment_body += "\n\n👀 Task completed and ready for review."
            elif status.lower() == "done":
                comment_body += "\n\n🎉 Task completed successfully!"
            
            url = f"{self.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{issue_number}/comments"
            comment_data = {"body": comment_body}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=comment_data) as response:
                    if response.status == 201:
                        print(f"[OK] Updated issue #{issue_number} status to '{column_name}'")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"[ERROR] Failed to add status comment: {response.status} - {error_text}")
                        return moved  # Return True if column move succeeded
                        
        except Exception as e:
            print(f"[ERROR] Error updating issue status: {e}")
            return False
    
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

    async def _check_existing_issues(self) -> List[str]:
        """Check for existing issues to prevent duplicates"""
        try:
            url = f"{self.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues"
            params = {"state": "open", "labels": "ai-factory", "per_page": 100}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        issues = await response.json()
                        existing_titles = [issue['title'] for issue in issues]
                        print(f"[INFO] Found {len(existing_titles)} existing ai-factory issues")
                        return existing_titles
                    else:
                        print(f"[WARNING] Failed to check existing issues: {response.status}")
                        return []
        except Exception as e:
            print(f"[WARNING] Error checking existing issues: {e}")
            return []

    async def dispatch_backlog(self, backlog_path: str = "product/BACKLOG.yml") -> Dict[str, List[str]]:
        """Main dispatch function: reads backlog and creates GitHub Issues"""
        try:
            # Check for existing issues to prevent duplicates
            existing_titles = await self._check_existing_issues()
            
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
                    # Check if this issue already exists
                    proposed_title = f"[{epic_title}] {task['task']}"
                    if proposed_title in existing_titles:
                        print(f"[SKIP] Issue already exists: {proposed_title}")
                        continue
                    
                    issue_number = await self.create_issue_from_task(task, epic_title)
                    if issue_number:
                        epic_issues.append(issue_number)
                        
                        # Auto-assign to appropriate agent
                        assigned_agent = self._assign_agent_to_task(task, epic_title)
                        if assigned_agent:
                            await self._assign_issue_to_agent(issue_number, assigned_agent)
                        
                        # Add to project board if configured and set to "To Do" status
                        if self.config.project_id:
                            await self.add_issue_to_project(issue_number)
                            await self.update_issue_status(issue_number, "to_do")
                        
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
    repo_owner = os.getenv('REPO_OWNER', 'AmosPulse')  # Changed from GITHUB_REPO_OWNER
    repo_name = os.getenv('REPO_NAME', 'proof-stamp')   # Changed from GITHUB_REPO_NAME
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
