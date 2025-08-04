# 🚀 AI Factory Quick Setup (15 Minutes)

> **For detailed instructions, see [AI_FACTORY_BLUEPRINT.md](./AI_FACTORY_BLUEPRINT.md)**

## ⚡ Super Quick Checklist

### **1. GitHub Project (2 min)**
- [ ] Create new GitHub Project (Board template)
- [ ] Get Project ID: F12 → Network → Find `PVT_...` in GraphQL response

### **2. Personal Access Token (2 min)**
- [ ] Go to: https://github.com/settings/tokens
- [ ] Create token with scopes: `repo`, `project`, `workflow`
- [ ] Copy token (starts with `ghp_`)

### **3. Repository Secrets (3 min)**
Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`

Add these 3 secrets:
- [ ] **`CLAUDE_API_KEY`**: Your Anthropic API key (`sk-ant-...`)
- [ ] **`REPO_TOKEN`**: Your Personal Access Token (`ghp_...`)
- [ ] **`PROJECT_ID`**: Your Project board ID (`PVT_...`)

### **4. Copy Files (5 min)**
Copy these files to your repository:

**Essential Files:**
```
.github/workflows/ai-ci.yml    # GitHub Actions workflow
mcp/github_integration.py      # GitHub API integration
dispatch.py                    # Main dispatch script
requirements.txt               # Python dependencies
product/BACKLOG.yml           # Your tasks (customize this!)
```

### **5. Test (3 min)**
- [ ] Push changes to repository
- [ ] Check GitHub Actions tab (workflow should run)
- [ ] Check Issues tab (new issues should appear)
- [ ] Check Project board (issues should be added as cards)

---

## 📁 Minimal File Set

If you want the absolute minimum setup, copy these 5 files:

1. **`.github/workflows/ai-ci.yml`** - The automation trigger
2. **`mcp/github_integration.py`** - GitHub API handler  
3. **`dispatch.py`** - Main script
4. **`requirements.txt`** - Dependencies
5. **`product/BACKLOG.yml`** - Your tasks

Everything else is optional (but recommended for full functionality).

---

## 🔧 Essential File Contents

### **`.github/workflows/ai-ci.yml`**
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
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: claude /orchestrator plan
      - run: python dispatch.py
```

### **`requirements.txt`**
```
aiohttp
PyYAML
asyncio
```

### **`product/BACKLOG.yml`** (Example)
```yaml
backlog:
  epic_1_setup:
    title: "Project Setup"
    description: "Initial project configuration"
    priority: "high"
    tasks:
      - task: "Create project structure"
        description: "Set up basic project directories and files"
        priority: "high"
        estimated_hours: 4
        
      - task: "Configure development environment"
        description: "Set up development tools and dependencies"
        priority: "medium"
        estimated_hours: 2
```

---

## ✅ Success Indicators

**After setup, you should see:**
- ✅ GitHub Actions workflow runs successfully
- ✅ New GitHub Issues created from your BACKLOG.yml
- ✅ Issues appear as cards on your Project board
- ✅ No error messages in workflow logs

**If something fails:**
1. Check repository secrets are set correctly
2. Verify Project ID format (starts with `PVT_`)
3. Ensure Personal Access Token has required scopes
4. Review workflow logs for specific error messages

---

## 🆘 Quick Fixes

**403 Permission Error:**
- Recreate Personal Access Token with `repo`, `project`, `workflow` scopes

**Project ID Not Found:**
- Get correct Project ID: F12 → Network → Find GraphQL response with `PVT_...`

**No Issues Created:**
- Check BACKLOG.yml format matches example above
- Verify REPO_TOKEN secret is set (not GITHUB_TOKEN)

---

## 🎯 What Happens Next

Once setup is complete:
1. **Every push** triggers the automation
2. **New tasks in BACKLOG.yml** become GitHub Issues
3. **Issues automatically added** to your Project board
4. **AI agents can work** on the created issues
5. **Zero manual intervention** required

**Setup once → Works forever!** 🚀

---

*For complete details, troubleshooting, and advanced features, see [AI_FACTORY_BLUEPRINT.md](./AI_FACTORY_BLUEPRINT.md)*
