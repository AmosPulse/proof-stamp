#!/usr/bin/env python3
"""
Agent Workflow System - Manages agent task execution and status updates
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Any
from github_integration import GitHubIntegration, load_github_config

class AgentWorkflow:
    def __init__(self, github_integration: GitHubIntegration):
        self.github = github_integration
        self.active_agents = {}  # agent_name -> {issue_number, start_time, status}
        
    async def simulate_agent_work(self, agent_name: str, issue_number: str, estimated_hours: float = 2.0):
        """Simulate an agent working on a task with realistic timing"""
        try:
            print(f"[{agent_name}] Starting work on issue #{issue_number}")
            
            # Move to In Progress
            await self.github.update_issue_status(issue_number, "in_progress", agent_name)
            
            # Track active work
            self.active_agents[f"{agent_name}_{issue_number}"] = {
                "agent": agent_name,
                "issue": issue_number,
                "start_time": time.time(),
                "status": "in_progress",
                "estimated_duration": estimated_hours * 3600  # Convert to seconds
            }
            
            # Simulate work time (scaled down for demo - use 1/60th of estimated time)
            work_duration = (estimated_hours * 60)  # 1 minute per estimated hour
            work_duration += random.uniform(-30, 30)  # Add some randomness
            work_duration = max(30, work_duration)  # Minimum 30 seconds
            
            print(f"[{agent_name}] Working for {work_duration:.1f} seconds...")
            await asyncio.sleep(work_duration)
            
            # Move to Review
            await self.github.update_issue_status(issue_number, "review", agent_name)
            self.active_agents[f"{agent_name}_{issue_number}"]["status"] = "review"
            
            # Review time (shorter)
            review_duration = random.uniform(10, 30)
            print(f"[{agent_name}] In review for {review_duration:.1f} seconds...")
            await asyncio.sleep(review_duration)
            
            # Move to Done
            await self.github.update_issue_status(issue_number, "done", agent_name)
            
            # Remove from active tracking
            del self.active_agents[f"{agent_name}_{issue_number}"]
            
            print(f"[{agent_name}] Completed issue #{issue_number}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Agent {agent_name} failed on issue #{issue_number}: {e}")
            return False
    
    async def start_agent_on_issue(self, issue_info: Dict[str, Any]):
        """Start an agent working on a specific issue"""
        agent_name = issue_info.get("agent")
        issue_number = issue_info.get("issue")
        estimated_hours = issue_info.get("estimated_hours", 2.0)
        
        if not agent_name or not issue_number:
            print("[ERROR] Missing agent or issue information")
            return False
        
        # Start the work asynchronously
        task = asyncio.create_task(
            self.simulate_agent_work(agent_name, issue_number, estimated_hours)
        )
        
        return task
    
    def get_active_work_status(self) -> Dict[str, Any]:
        """Get status of all active agent work"""
        current_time = time.time()
        status = {
            "active_agents": len(self.active_agents),
            "work_details": {}
        }
        
        for key, work_info in self.active_agents.items():
            elapsed = current_time - work_info["start_time"]
            progress = min(100, (elapsed / work_info["estimated_duration"]) * 100)
            
            status["work_details"][key] = {
                "agent": work_info["agent"],
                "issue": work_info["issue"],
                "status": work_info["status"],
                "elapsed_time": f"{elapsed:.1f}s",
                "progress": f"{progress:.1f}%"
            }
        
        return status

async def demo_agent_workflow(max_concurrent_agents: int = 3):
    """Demo the agent workflow system"""
    print("🤖 AGENT WORKFLOW SYSTEM DEMO")
    print("=" * 50)
    
    # Load GitHub configuration
    config = load_github_config()
    if not config:
        print("[ERROR] GitHub configuration not found")
        return False
    
    github = GitHubIntegration(config)
    workflow = AgentWorkflow(github)
    
    # Demo issues with their assigned agents (from our earlier analysis)
    demo_issues = [
        {"agent": "architect", "issue": "109", "estimated_hours": 4.0},
        {"agent": "qa-bot", "issue": "110", "estimated_hours": 2.0},
        {"agent": "dashboard-smith", "issue": "117", "estimated_hours": 8.0},
        {"agent": "release-bot", "issue": "118", "estimated_hours": 3.0},
        {"agent": "stuck-guard", "issue": "115", "estimated_hours": 3.0},
    ]
    
    print(f"Starting {len(demo_issues)} agents with max {max_concurrent_agents} concurrent...")
    print()
    
    active_tasks = []
    
    # Start agents (respecting concurrency limit)
    for i, issue_info in enumerate(demo_issues):
        if len(active_tasks) >= max_concurrent_agents:
            # Wait for one to complete
            done, pending = await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)
            active_tasks = list(pending)
        
        # Start new agent
        task = await workflow.start_agent_on_issue(issue_info)
        if task:
            active_tasks.append(task)
        
        # Show status
        status = workflow.get_active_work_status()
        print(f"Active agents: {status['active_agents']}")
    
    # Wait for all remaining tasks to complete
    if active_tasks:
        await asyncio.gather(*active_tasks)
    
    print("\n" + "=" * 50)
    print("🎉 All agents completed their work!")
    print("Check your GitHub project board - issues should have moved through:")
    print("  To Do → In Progress → Review → Done")
    
    return True

if __name__ == "__main__":
    asyncio.run(demo_agent_workflow())