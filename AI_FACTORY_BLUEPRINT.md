# 🏭 AI Factory Blueprint
## Complete Setup Guide for Automated GitHub Issue Management with Claude CLI

> **Mission**: Create a fully automated AI factory that reads project backlogs, creates GitHub Issues, manages Project boards, and enables AI agents to work on tasks autonomously.

---

## 🎯 What This Factory Does

### **Automated Workflow:**
1. **Push to GitHub** → Triggers GitHub Actions
2. **Claude orchestrator** runs (`claude /orchestrator plan`)
3. **Python dispatch script** reads `product/BACKLOG.yml`
4. **Creates GitHub Issues** for each backlog task
5. **Adds issues to Project board** automatically
6. **AI agents can work on issues** → Create PRs → Close issues

### **Key Benefits:**
- ✅ **Set once, runs forever** - No manual intervention needed
- ✅ **Automatic task management** - Backlog → Issues → Project board
- ✅ **AI agent integration** - Agents work on real GitHub Issues
- ✅ **Complete automation** - From planning to execution

---

## 📋 Prerequisites

### **Required Accounts & Tools:**
- GitHub account with repository access
- Anthropic API account with Claude API key
- GitHub Project board (V2 - new projects)
- Basic knowledge of GitHub Actions and secrets

### **Required Permissions:**
- Repository admin access (for secrets and Actions)
- Personal Access Token with specific scopes (detailed below)

---

## 🚀 Quick Setup Checklist

### **Phase 1: Repository Setup (5 minutes)**
- [ ] Create/clone repository
- [ ] Copy AI factory files (see File Structure section)
- [ ] Create GitHub Project board
- [ ] Get Project board ID

### **Phase 2: Secrets Configuration (5 minutes)**
- [ ] Create Personal Access Token
- [ ] Add CLAUDE_API_KEY secret
- [ ] Add REPO_TOKEN secret
- [ ] Add PROJECT_ID secret

### **Phase 3: Content Setup (5 minutes)**
- [ ] Create product/VISION.md
- [ ] Create product/ROADMAP.yml
- [ ] Create product/BACKLOG.yml
- [ ] Create .claude/agents/ (optional)

### **Phase 4: Testing (2 minutes)**
- [ ] Push changes to trigger workflow
- [ ] Verify issues are created
- [ ] Verify project board integration

**Total Setup Time: ~15-20 minutes**

---

## 📁 Complete File Structure

```
your-project/
├── .github/workflows/
│   └── ai-ci.yml                    # GitHub Actions workflow
├── .claude/agents/
│   └── file-maker.md               # Example agent (optional)
├── mcp/
│   ├── github_integration.py       # GitHub API integration
│   ├── orchestrator.py            # Task orchestration engine
│   ├── cost_governor.py           # Cost management
│   └── stuck_guard.py             # Timeout protection
├── product/
│   ├── VISION.md                   # Project vision
│   ├── ROADMAP.yml                # Project roadmap
│   └── BACKLOG.yml                # Task backlog (auto-converted to issues)
├── dispatch.py                     # Main dispatch script
├── requirements.txt                # Python dependencies
├── GITHUB_SETUP.md                # Setup instructions
├── .mcp-config.toml               # MCP configuration
└── README.md                       # Project overview
```

---

## 🔧 Detailed Setup Instructions

### **Step 1: Create GitHub Project Board**

1. Go to: https://github.com/users/YOUR_USERNAME/projects
2. Click **"New project"**
3. Choose **"Board"** template
4. Name it (e.g., "AI Factory Tasks")
5. Set visibility (Public/Private)
6. **Get Project ID**:
   - Open browser Developer Tools (F12)
   - Go to Network tab, refresh page
   - Look for GraphQL requests containing project data
   - Find `id` field starting with `PVT_` - this is your PROJECT_ID

### **Step 2: Create Personal Access Token**

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. **Token name**: `AI Factory Automation`
4. **Expiration**: No expiration (or your preference)
5. **Required scopes**:
   - ✅ `repo` (Full control of repositories)
   - ✅ `project` (Full control of projects)
   - ✅ `workflow` (Update GitHub Action workflows)
6. Click **"Generate token"**
7. **Copy token** (starts with `ghp_`) - you'll need it for secrets

### **Step 3: Add Repository Secrets**

Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`

Add these **3 required secrets**:

1. **`CLAUDE_API_KEY`**
   - Value: Your Anthropic API key (starts with `sk-ant-`)

2. **`REPO_TOKEN`**
   - Value: Your Personal Access Token from Step 2 (starts with `ghp_`)

3. **`PROJECT_ID`**
   - Value: Your Project board node ID from Step 1 (starts with `PVT_`)

### **Step 4: Copy Core Files**

Copy these files to your repository (exact content provided below):

#### **`.github/workflows/ai-ci.yml`**
```yaml
name: ai-pipeline
on: [push]

jobs:
  plan:
    runs-on: windows-latest
    env:
      ANTHROPIC_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
      REPO_TOKEN: ${{ secrets.REPO_TOKEN }}
      GITHUB_REPO_OWNER: ${{ github.repository_owner }}
      GITHUB_REPO_NAME: ${{ github.event.repository.name }}
      PROJECT_ID: ${{ secrets.PROJECT_ID }}
    steps:
      - uses: actions/checkout@v4
      - run: npm install -g @anthropic-ai/claude-code
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install Python dependencies
        run: pip install -r requirements.txt
      - run: claude /orchestrator plan
      - name: Dispatch backlog to GitHub Issues
        run: python dispatch.py
```

#### **`requirements.txt`**
```
aiohttp
PyYAML
asyncio
```

#### **`dispatch.py`**
```python
#!/usr/bin/env python3
"""
AI Factory Dispatch Script
Reads BACKLOG.yml and creates GitHub Issues automatically
"""

import asyncio
import sys
import os

# Add mcp directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp'))

from github_integration import GitHubIntegration, load_github_config

async def dispatch():
    """Main dispatch function"""
    print("[AI Factory] Dispatch Starting...")
    print("=" * 50)
    
    # Load GitHub configuration
    config = load_github_config()
    if not config:
        print("[ERROR] GitHub configuration failed. Required environment variables:")
        print("   - REPO_TOKEN: Personal Access Token")
        print("   - GITHUB_REPO_OWNER: Repository owner")
        print("   - GITHUB_REPO_NAME: Repository name")
        print("   - PROJECT_ID: Project board ID (optional)")
        return False
    
    print(f"[OK] GitHub config loaded:")
    print(f"   Repository: {config.repo_owner}/{config.repo_name}")
    print(f"   Project ID: {config.project_id or 'Not configured'}")
    print()
    
    # Create GitHub integration and dispatch backlog
    github = GitHubIntegration(config)
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
```

#### **`.mcp-config.toml`**
```toml
[mcp]
name = "ai-factory"
version = "1.0.0"
description = "AI Factory Orchestrator"
```

### **Step 5: Create Product Files**

#### **`product/VISION.md`**
```markdown
# Project Vision

## Hello-World Milestone

Create a simple "Hello World" demonstration to test the AI factory automation system.

### Goals:
- Test orchestrator task creation
- Verify GitHub Issues integration
- Validate Project board automation
- Demonstrate end-to-end AI factory workflow

### Success Criteria:
- Issues created automatically from backlog
- Project board updated with new tasks
- Agents can work on generated issues
```

#### **`product/ROADMAP.yml`**
```yaml
roadmap:
  - epic: "Hello-World Demo"
    description: "Initial demonstration of AI factory capabilities"
    priority: "high"
    status: "active"
```

#### **`product/BACKLOG.yml`** (Example)
```yaml
backlog:
  epic_1_core_infrastructure:
    title: "Core Infrastructure Setup"
    description: "Essential system components and configurations"
    priority: "high"
    tasks:
      - task: "Database schema design and migrations"
        description: "Design and implement core database structure"
        priority: "high"
        estimated_hours: 8
        
      - task: "MCP server configuration and testing"
        description: "Set up and test MCP server connectivity"
        priority: "medium"
        estimated_hours: 4
        
      - task: "Email notification service integration"
        description: "Implement email alerts for system events"
        priority: "low"
        estimated_hours: 6

  epic_2_orchestrator_core:
    title: "Orchestrator Core Features"
    description: "Task management and execution engine"
    priority: "high"
    tasks:
      - task: "Task dependency resolution engine"
        description: "Implement task dependency tracking and resolution"
        priority: "high"
        estimated_hours: 12
        
      - task: "Priority-based scheduling algorithm"
        description: "Create intelligent task prioritization system"
        priority: "medium"
        estimated_hours: 10
        
      - task: "Resource allocation and limiting"
        description: "Implement resource management and throttling"
        priority: "medium"
        estimated_hours: 8
```

---

## 🔄 How It Works (Technical Details)

### **GitHub Actions Workflow:**
1. **Trigger**: Any push to repository
2. **Environment**: Windows runner with Python 3.9
3. **Dependencies**: Claude CLI + Python packages
4. **Steps**:
   - Install Claude CLI globally
   - Set up Python environment
   - Install Python dependencies
   - Run `claude /orchestrator plan`
   - Run `python dispatch.py`

### **Dispatch Process:**
1. **Load Configuration**: Read environment variables
2. **Parse Backlog**: Read and parse `product/BACKLOG.yml`
3. **Create Issues**: For each epic → For each task → Create GitHub Issue
4. **Add to Project**: Use GraphQL API to add issues to project board
5. **Summary**: Report total issues created

### **GitHub API Integration:**
- **REST API**: Create issues (`POST /repos/{owner}/{repo}/issues`)
- **GraphQL API**: Add issues to project board (`addProjectV2ItemById`)
- **Authentication**: Personal Access Token with required scopes
- **Rate Limiting**: Built-in delays between API calls

---

## 🛠️ Core Components Deep Dive

### **GitHub Integration (`mcp/github_integration.py`)**
- **Purpose**: Handle all GitHub API interactions
- **Key Functions**:
  - `create_github_issue()`: Creates issues via REST API
  - `add_issue_to_project()`: Adds issues to project board via GraphQL
  - `dispatch_backlog()`: Main orchestration function
- **Error Handling**: Comprehensive error logging and recovery
- **Rate Limiting**: Automatic delays to respect API limits

### **Orchestrator (`mcp/orchestrator.py`)**
- **Purpose**: Task management and execution engine
- **Features**:
  - Task dependency resolution
  - Priority-based scheduling
  - Resource allocation
  - Cost governance
  - Stuck task detection
- **Integration**: Works with Claude CLI for AI-powered task execution

### **Cost Governor (`mcp/cost_governor.py`)**
- **Purpose**: Monitor and control API costs
- **Features**:
  - Budget tracking
  - Cost alerts
  - Automatic throttling
  - Usage reporting

### **Stuck Guard (`mcp/stuck_guard.py`)**
- **Purpose**: Detect and handle stuck tasks
- **Features**:
  - Timeout detection
  - Automatic task recovery
  - Alert notifications
  - Health monitoring

---

## 🧪 Testing Your Setup

### **Quick Test (2 minutes):**
1. **Trigger workflow**: Push any change to repository
2. **Check Actions**: Go to Actions tab, verify workflow runs successfully
3. **Check Issues**: Go to Issues tab, verify new issues are created
4. **Check Project**: Go to your project board, verify issues appear as cards

### **Expected Results:**
- ✅ GitHub Actions workflow completes successfully
- ✅ New GitHub Issues created (number depends on your BACKLOG.yml)
- ✅ Issues automatically added to project board
- ✅ No error messages in workflow logs

### **Common Issues & Solutions:**

**❌ 403 "Resource not accessible by integration"**
- **Cause**: REPO_TOKEN lacks required permissions
- **Fix**: Recreate token with `repo`, `project`, `workflow` scopes

**❌ "Could not resolve to a node with the global id"**
- **Cause**: Incorrect PROJECT_ID
- **Fix**: Get correct project node ID (starts with `PVT_`)

**❌ "REPO_TOKEN environment variable not set"**
- **Cause**: Missing or incorrectly named repository secret
- **Fix**: Add REPO_TOKEN secret (not GITHUB_TOKEN)

**❌ Unicode encoding errors**
- **Cause**: Emoji characters in output on Windows runners
- **Fix**: Use text prefixes like [OK], [ERROR] instead of emojis

---

## 🔄 Customization Guide

### **Modify Backlog Structure:**
Edit `product/BACKLOG.yml` to match your project needs:
```yaml
backlog:
  your_epic_name:
    title: "Your Epic Title"
    description: "Epic description"
    priority: "high|medium|low"
    tasks:
      - task: "Task name"
        description: "Task description"
        priority: "high|medium|low"
        estimated_hours: 8
```

### **Add Custom Agents:**
Create agents in `.claude/agents/`:
```markdown
# Agent Name

You are a specialized agent for [specific task].

## Role
[Define the agent's role and responsibilities]

## Guidelines
- [Specific guidelines for this agent]
- [Best practices to follow]
```

### **Modify Workflow Triggers:**
Edit `.github/workflows/ai-ci.yml`:
```yaml
# Run on specific branches only
on:
  push:
    branches: [ main, develop ]

# Run on schedule
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
```

### **Add Environment-Specific Configuration:**
```yaml
# Different settings for different environments
env:
  ENVIRONMENT: ${{ github.ref == 'refs/heads/main' && 'production' || 'development' }}
  MAX_ISSUES_PER_RUN: ${{ github.ref == 'refs/heads/main' && '50' || '10' }}
```

---

## 📊 Monitoring & Maintenance

### **Regular Checks:**
- **Weekly**: Review created issues and project board
- **Monthly**: Check API usage and costs
- **Quarterly**: Update dependencies and review automation efficiency

### **Key Metrics to Monitor:**
- Issues created per run
- Project board update success rate
- GitHub Actions workflow success rate
- API rate limit usage

### **Maintenance Tasks:**
- Update Claude CLI version
- Refresh Personal Access Token (if it expires)
- Review and clean up completed issues
- Update backlog with new epics/tasks

---

## 🚀 Advanced Features

### **Multi-Repository Support:**
Extend the system to manage multiple repositories:
```python
# In dispatch.py
repositories = [
    {"owner": "user1", "repo": "project1"},
    {"owner": "user2", "repo": "project2"}
]
```

### **Custom Issue Templates:**
Create issue templates in `.github/ISSUE_TEMPLATE/`:
```markdown
---
name: AI Factory Task
about: Automatically created task from backlog
labels: ai-factory, task
---

## Task Description
{{ task.description }}

## Epic
{{ epic.title }}

## Priority
{{ task.priority }}

## Estimated Hours
{{ task.estimated_hours }}
```

### **Slack/Discord Integration:**
Add notifications to your team channels:
```python
# Add to github_integration.py
async def send_notification(self, message):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if webhook_url:
        await self.send_slack_message(webhook_url, message)
```

---

## 📚 Troubleshooting Guide

### **Debug Mode:**
Enable detailed logging by adding to workflow:
```yaml
env:
  DEBUG: true
  PYTHONPATH: ${{ github.workspace }}
```

### **Local Testing:**
Test components locally:
```bash
# Set environment variables
export REPO_TOKEN="your_token"
export GITHUB_REPO_OWNER="your_username"
export GITHUB_REPO_NAME="your_repo"
export PROJECT_ID="your_project_id"

# Run dispatch script
python dispatch.py
```

### **API Rate Limits:**
Monitor GitHub API usage:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.github.com/rate_limit
```

---

## 🎯 Success Metrics

### **Setup Success Indicators:**
- ✅ All 3 repository secrets configured correctly
- ✅ GitHub Actions workflow runs without errors
- ✅ Issues created automatically from backlog
- ✅ Project board shows new issue cards
- ✅ No authentication or permission errors

### **Operational Success Indicators:**
- ✅ Consistent issue creation on every push
- ✅ Project board stays synchronized
- ✅ AI agents can work on created issues
- ✅ Workflow completes in under 5 minutes
- ✅ Zero manual intervention required

---

## 🔄 Migration Guide

### **From Existing Project:**
1. **Backup**: Create backup of existing project
2. **Copy Files**: Add AI factory files to existing repository
3. **Configure Secrets**: Add required repository secrets
4. **Test**: Run on separate branch first
5. **Deploy**: Merge to main branch when confirmed working

### **To New Repository:**
1. **Clone**: Clone this repository as template
2. **Customize**: Update product files for your project
3. **Configure**: Set up secrets and project board
4. **Deploy**: Push to trigger first automation run

---

## 📞 Support & Resources

### **Documentation:**
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub GraphQL API](https://docs.github.com/en/graphql)
- [Anthropic Claude API](https://docs.anthropic.com/)

### **Community:**
- GitHub Discussions for questions
- Issues for bug reports
- Pull Requests for improvements

---

## 🎉 Conclusion

This AI Factory Blueprint provides everything needed to set up a fully automated GitHub issue management system in **15-20 minutes**. The system is:

- **🔄 Fully Automated**: Set once, runs forever
- **🎯 Production Ready**: Handles errors, rate limits, and edge cases
- **📈 Scalable**: Easily extend to multiple repositories and teams
- **🛠️ Customizable**: Adapt to any project structure or workflow
- **📚 Well Documented**: Complete instructions and troubleshooting

**Next Project Setup Time: ~15 minutes** (vs. days of manual setup)

---

*Created with ❤️ for the AI Factory automation system*
*Last updated: 2025-01-04*
