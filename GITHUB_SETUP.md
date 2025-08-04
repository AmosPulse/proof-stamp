# GitHub Integration Setup Guide

This guide helps you set up the automatic GitHub integration for the AI Factory system. **Set it up once and it handles everything automatically!**

## What It Does Automatically

✅ **Reads BACKLOG.yml** → **Creates GitHub Issues**  
✅ **Updates your Project board** with new issues  
✅ **Tracks task progress** through GitHub workflow  
✅ **Runs on every push** via GitHub Actions  

## One-Time Setup Steps

### 1. Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name like "AI Factory Orchestrator"
4. Select these scopes:
   - `repo` (Full control of private repositories)
   - `project` (Full control of projects)
   - `workflow` (Update GitHub Action workflows)

### 2. Add Repository Secrets

Go to your repository Settings → Secrets and variables → Actions → Repository secrets:

1. **CLAUDE_API_KEY** ✅ (Already set)
2. **GITHUB_PROJECT_ID** ➕ (Add this)
   - Your project ID from: https://github.com/users/AmosPulse/projects/6/
   - To find the ID: Go to your project → Settings → copy the project ID

### 3. Verify Project Board Connection

Your project board at https://github.com/users/AmosPulse/projects/6/ should be:
- Connected to the `proof-stamp` repository
- Have columns like: "Todo", "In Progress", "Done" (or similar)

## How It Works

1. **Push changes** → GitHub Actions triggers
2. **Claude orchestrator** updates BACKLOG.yml  
3. **Python dispatch script** reads backlog
4. **Creates GitHub Issues** for each task
5. **Adds issues to Project board** automatically
6. **Agents can work on issues** → Create PRs
7. **PRs merge** → Issues close → Board updates

## Testing the Setup

After setup, push any change to trigger the workflow:

```bash
git add .
git commit -m "test: trigger AI factory dispatch"
git push
```

Check:
1. GitHub Actions tab for workflow success
2. Issues tab for new issues created from backlog
3. Project board for new cards

## Troubleshooting

**No issues created?**
- Check GITHUB_TOKEN has correct permissions
- Verify GITHUB_PROJECT_ID is set correctly
- Check GitHub Actions logs for errors

**Issues created but not on project board?**
- Verify GITHUB_PROJECT_ID matches your project
- Check project is connected to the repository
- Ensure token has `project` scope

## Files Created

- `mcp/github_integration.py` - Core GitHub API integration
- `dispatch.py` - Main dispatch script  
- `requirements.txt` - Python dependencies
- `.github/workflows/ai-ci.yml` - Updated workflow

---

**🎉 Once set up, the system runs automatically on every push!**
