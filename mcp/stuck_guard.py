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
        self.running = False

    async def register_task(self, task_id: str, timeout: Optional[float] = None) -> None:
        current_time = time.time()
        monitor = TaskMonitor(
            task_id=task_id,
            start_time=current_time,
            last_progress=current_time,
            timeout_threshold=timeout or self.default_timeout
        )
        self.monitored_tasks[task_id] = monitor
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

    async def start_monitoring(self) -> None:
        self.running = True
        print("[StuckGuard] Started monitoring")
        
        while self.running:
            await self.check_stuck_tasks()
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