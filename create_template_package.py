#!/usr/bin/env python3
"""
AI Factory Template Package Generator

Creates a complete template package with all files needed to start a new AI Factory project.
This script copies all essential files to a template directory that can be zipped and reused.
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

def create_template_package():
    """Create a complete AI Factory template package"""
    
    print("[AI Factory] Template Package Generator")
    print("=" * 50)
    
    # Define source and destination paths
    source_dir = Path(".")
    template_dir = Path("AI_FACTORY_TEMPLATE")
    zip_name = f"AI_Factory_Template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    # Clean up existing template directory
    if template_dir.exists():
        print(f"[INFO] Removing existing template directory: {template_dir}")
        shutil.rmtree(template_dir)
    
    # Create template directory structure
    print(f"[INFO] Creating template directory: {template_dir}")
    template_dir.mkdir()
    
    # Define files and directories to include in template
    template_files = {
        # Core automation files
        ".github/workflows/ai-ci.yml": ".github/workflows/ai-ci.yml",
        "mcp/github_integration.py": "mcp/github_integration.py",
        "mcp/orchestrator.py": "mcp/orchestrator.py", 
        "mcp/cost_governor.py": "mcp/cost_governor.py",
        "mcp/stuck_guard.py": "mcp/stuck_guard.py",
        "dispatch.py": "dispatch.py",
        "requirements.txt": "requirements.txt",
        ".mcp-config.toml": ".mcp-config.toml",
        
        # Documentation files
        "README.md": "README.md",
        "AI_FACTORY_BLUEPRINT.md": "AI_FACTORY_BLUEPRINT.md",
        "QUICK_SETUP.md": "QUICK_SETUP.md",
        "GITHUB_SETUP.md": "GITHUB_SETUP.md",
        "AI_FACTORY_TEMPLATE_MANIFEST.md": "AI_FACTORY_TEMPLATE_MANIFEST.md",
        
        # Project content files (templates)
        "product/VISION.md": "product/VISION.md",
        "product/ROADMAP.yml": "product/ROADMAP.yml",
        "product/BACKLOG.yml": "product/BACKLOG.yml",
        
        # Optional agent files
        ".claude/agents/file-maker.md": ".claude/agents/file-maker.md",
    }
    
    # Copy files to template directory
    copied_files = []
    missing_files = []
    
    for source_file, dest_file in template_files.items():
        source_path = source_dir / source_file
        dest_path = template_dir / dest_file
        
        if source_path.exists():
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            copied_files.append(dest_file)
            print(f"[OK] Copied: {source_file}")
        else:
            missing_files.append(source_file)
            print(f"[WARNING] Missing: {source_file}")
    
    # Create template README
    create_template_readme(template_dir)
    
    # Create zip file
    print(f"\n[INFO] Creating zip file: {zip_name}")
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                file_path = Path(root) / file
                arc_name = file_path.relative_to(template_dir)
                zipf.write(file_path, arc_name)
    
    # Summary
    print("\n" + "=" * 50)
    print("[SUCCESS] Template Package Created Successfully!")
    print(f"📁 Template directory: {template_dir}")
    print(f"📦 Zip file: {zip_name}")
    if missing_files:
        print(f"Missing files: {len(missing_files)}")
        for file in missing_files:
            print(f"   - {file}")
    
    print(f"\nReady to deploy! Extract {zip_name} to any new repository.")
    print("See AI_FACTORY_TEMPLATE_MANIFEST.md for deployment instructions.")
    
    return zip_name, len(copied_files), len(missing_files)

def create_template_readme(template_dir):
    """Create a README for the template package"""
    
    readme_content = """# AI Factory Template Package

> **Complete template for rapid AI Factory deployment on new projects**

## 🚀 Quick Start

1. **Extract this template** to your new repository
2. **Follow preparation steps** in `AI_FACTORY_BLUEPRINT.md`
3. **Customize files** in `product/` directory for your project
4. **Add repository secrets** (CLAUDE_API_KEY, REPO_TOKEN, PROJECT_ID)
5. **Push to GitHub** - automation starts immediately!

## 📁 What's Included

- ✅ **Complete automation system** - GitHub Actions + Python scripts
- ✅ **Full documentation** - Setup guides and troubleshooting
- ✅ **Project templates** - Vision, roadmap, backlog files
- ✅ **AI agent support** - Claude CLI integration
- ✅ **Production tested** - Working system from day one

## 📚 Key Files

- `AI_FACTORY_BLUEPRINT.md` - **Complete setup guide**
- `QUICK_SETUP.md` - **15-minute setup checklist**
- `product/BACKLOG.yml` - **Customize this with your tasks**
- `.github/workflows/ai-ci.yml` - **Automation workflow**

## ⏱️ Setup Time

**Total: 15-20 minutes**
- Preparation: 5 minutes
- File customization: 5 minutes  
- GitHub setup: 5 minutes
- Testing: 5 minutes

## 🎯 What You Get

- **Automated GitHub Issues** from your backlog
- **Project board integration** with visual task management
- **AI agent compatibility** for autonomous work
- **Zero manual intervention** after setup

---

**🚀 Ready to build? Start with `AI_FACTORY_BLUEPRINT.md`!**

*Template version: 1.0*
*Created: """ + datetime.now().strftime('%Y-%m-%d') + """*
"""
    
    readme_path = template_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("[OK] Created template README.md")

if __name__ == "__main__":
    try:
        zip_name, copied_count, missing_count = create_template_package()
        
        if missing_count == 0:
            print(f"\n[SUCCESS] Perfect! All {copied_count} files copied successfully.")
            print(f"[READY] Your template package '{zip_name}' is ready for reuse!")
        else:
            print(f"\n[WARNING] Template created with {missing_count} missing files.")
            print("Check the warnings above and ensure all core files exist.")
            
    except Exception as e:
        print(f"\n[ERROR] Error creating template package: {e}")
        print("Please check file permissions and try again.")
