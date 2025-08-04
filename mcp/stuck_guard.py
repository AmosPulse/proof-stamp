#!/usr/bin/env python3

import asyncio
import time
from typing import Dict, Optional, Set
from dataclasses import dataclass


@dataclass
class TaskMonitor:
    task_id: str
    start_time: float
    last_progress: float
    timeout_threshold: float = 300.0  # 5 minutes default
    max_idle_time: float = 60.0       # 1 minute without progress


class StuckGuard:
    def __init__(self, default_timeout: float = 300.0, check_interval: float = 30.0):
        self.default_timeout = default_timeout
        self.check_interval = check_interval
        self.monitored_tasks: Dict[str, TaskMonitor] = {}
        self.stuck_tasks: Set[str] = set()
        self.task_dependencies: Dict[str, Set[str]] = {}  # task_id -> set of dependency_ids
        self.running = False

    async def register_task(self, task_id: str, timeout: Optional[float] = None, dependencies: Optional[Set[str]] = None) -> None:
        current_time = time.time()
        monitor = TaskMonitor(
            task_id=task_id,
            start_time=current_time,
            last_progress=current_time,
            timeout_threshold=timeout or self.default_timeout
        )
        self.monitored_tasks[task_id] = monitor
        self.task_dependencies[task_id] = dependencies or set()
        print(f"[StuckGuard] Registered task: {task_id}")

    async def update_progress(self, task_id: str) -> None:
        if task_id in self.monitored_tasks:
            self.monitored_tasks[task_id].last_progress = time.time()
            if task_id in self.stuck_tasks:
                self.stuck_tasks.remove(task_id)
                print(f"[StuckGuard] Task {task_id} resumed progress")

    async def complete_task(self, task_id: str) -> None:
        if task_id in self.monitored_tasks:
            del self.monitored_tasks[task_id]
            self.stuck_tasks.discard(task_id)
            if task_id in self.task_dependencies:
                del self.task_dependencies[task_id]
            print(f"[StuckGuard] Task {task_id} completed and removed from monitoring")

    async def check_stuck_tasks(self) -> Set[str]:
        current_time = time.time()
        newly_stuck = set()
        
        for task_id, monitor in self.monitored_tasks.items():
            time_since_start = current_time - monitor.start_time
            time_since_progress = current_time - monitor.last_progress
            
            is_stuck = (
                time_since_start > monitor.timeout_threshold or
                time_since_progress > monitor.max_idle_time
            )
            
            if is_stuck and task_id not in self.stuck_tasks:
                newly_stuck.add(task_id)
                self.stuck_tasks.add(task_id)
                print(f"[StuckGuard] ALERT: Task {task_id} appears stuck!")
                print(f"  - Running for: {time_since_start:.1f}s")
                print(f"  - Idle for: {time_since_progress:.1f}s")
        
        return newly_stuck

    async def get_stuck_tasks(self) -> Set[str]:
        return self.stuck_tasks.copy()

    async def force_timeout_task(self, task_id: str) -> bool:
        if task_id in self.monitored_tasks:
            self.stuck_tasks.add(task_id)
            print(f"[StuckGuard] Force timeout applied to task: {task_id}")
            return True
        return False

    async def detect_dependency_cycles(self) -> Set[Set[str]]:
        """Detect circular dependencies using DFS"""
        cycles = set()
        visited = set()
        rec_stack = set()
        
        def dfs(task_id: str, path: list) -> Optional[list]:
            if task_id in rec_stack:
                # Found cycle - extract it
                cycle_start = path.index(task_id)
                return path[cycle_start:] + [task_id]
            
            if task_id in visited:
                return None
            
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)
            
            # Check dependencies
            for dep_id in self.task_dependencies.get(task_id, set()):
                if dep_id in self.task_dependencies:  # Only check monitored tasks
                    cycle = dfs(dep_id, path.copy())
                    if cycle:
                        cycles.add(frozenset(cycle))
            
            rec_stack.remove(task_id)
            path.pop()
            return None
        
        # Check all tasks
        for task_id in self.task_dependencies:
            if task_id not in visited:
                dfs(task_id, [])
        
        return {set(cycle) for cycle in cycles}

    async def check_dependency_blocks(self) -> Dict[str, str]:
        """Check for tasks blocked by dependencies and return blocking reasons"""
        blocked_tasks = {}
        
        for task_id, dependencies in self.task_dependencies.items():
            if task_id not in self.monitored_tasks:
                continue
                
            for dep_id in dependencies:
                # Check if dependency is stuck or failed
                if dep_id in self.stuck_tasks:
                    blocked_tasks[task_id] = f"Blocked by stuck dependency: {dep_id}"
                    break
                elif dep_id in self.monitored_tasks:
                    # Check if dependency has been running too long
                    dep_monitor = self.monitored_tasks[dep_id]
                    if time.time() - dep_monitor.start_time > dep_monitor.timeout_threshold:
                        blocked_tasks[task_id] = f"Blocked by timeout dependency: {dep_id}"
                        break
        
        return blocked_tasks

    async def start_monitoring(self) -> None:
        self.running = True
        print("[StuckGuard] Started monitoring")
        
        while self.running:
            await self.check_stuck_tasks()
            
            # Check for dependency cycles every 5 minutes
            if int(time.time()) % 300 == 0:  # Every 5 minutes
                cycles = await self.detect_dependency_cycles()
                if cycles:
                    print(f"[StuckGuard] ALERT: Dependency cycles detected: {cycles}")
                
                blocked = await self.check_dependency_blocks()
                if blocked:
                    print(f"[StuckGuard] ALERT: Tasks blocked by dependencies: {blocked}")
            
            await asyncio.sleep(self.check_interval)

    async def stop_monitoring(self) -> None:
        self.running = False
        print("[StuckGuard] Stopped monitoring")

    def get_status(self) -> Dict:
        return {
            "running": self.running,
            "monitored_tasks": len(self.monitored_tasks),
            "stuck_tasks": len(self.stuck_tasks),
            "task_details": {
                task_id: {
                    "running_time": time.time() - monitor.start_time,
                    "idle_time": time.time() - monitor.last_progress,
                    "is_stuck": task_id in self.stuck_tasks
                }
                for task_id, monitor in self.monitored_tasks.items()
            }
        }


async def main():
    guard = StuckGuard()
    
    await guard.register_task("test_task_1")
    await guard.register_task("test_task_2", timeout=60.0)
    
    monitoring_task = asyncio.create_task(guard.start_monitoring())
    
    await asyncio.sleep(5)
    await guard.update_progress("test_task_1")
    
    await asyncio.sleep(10)
    print("Status:", guard.get_status())
    
    await guard.complete_task("test_task_1")
    await guard.stop_monitoring()
    
    await monitoring_task


if __name__ == "__main__":
    asyncio.run(main())