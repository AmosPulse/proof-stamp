#!/usr/bin/env python3

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from stuck_guard import StuckGuard
from cost_governor import CostGovernor, CostCategory


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    id: str
    name: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    dependencies: Set[str] = field(default_factory=set)
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    max_retries: int = 3
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    result: Any = None


class Orchestrator:
    def __init__(self, max_concurrent_tasks: int = 5):
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        
        # Initialize monitoring components
        self.stuck_guard = StuckGuard(default_timeout=600.0)  # 10 minutes default
        self.cost_governor = CostGovernor()
        
        # System state
        self.running = False
        self.paused = False
        self.shutdown_requested = False
        
        print("[Orchestrator] Initialized with max concurrent tasks:", max_concurrent_tasks)

    def register_task_handler(self, task_type: str, handler: Callable) -> None:
        self.task_handlers[task_type] = handler
        print(f"[Orchestrator] Registered handler for task type: {task_type}")

    async def create_task(self, name: str, task_type: str, priority: TaskPriority = TaskPriority.MEDIUM,
                         dependencies: Optional[Set[str]] = None, estimated_cost: float = 0.0,
                         max_retries: int = 3, metadata: Optional[Dict[str, Any]] = None) -> str:
        task_id = str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            name=name,
            priority=priority,
            dependencies=dependencies or set(),
            estimated_cost=estimated_cost,
            max_retries=max_retries,
            metadata=metadata or {}
        )
        task.metadata["task_type"] = task_type
        
        self.tasks[task_id] = task
        
        # Register with stuck guard
        await self.stuck_guard.register_task(task_id)
        
        print(f"[Orchestrator] Created task {task_id}: {name}")
        return task_id

    async def _can_start_task(self, task: Task) -> Tuple[bool, Optional[str]]:
        # Check if system is paused
        if self.paused:
            return False, "System is paused"
        
        # Check concurrent task limit
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return False, "Maximum concurrent tasks reached"
        
        # Check if task is paused by cost governor
        if await self.cost_governor.is_task_paused(task.id):
            return False, "Task paused by cost governor"
        
        # Check dependencies
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False, f"Dependency {dep_id} not found"
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False, f"Dependency {dep_id} not completed"
        
        # Check if we have a handler for this task type
        task_type = task.metadata.get("task_type")
        if task_type not in self.task_handlers:
            return False, f"No handler registered for task type: {task_type}"
        
        return True, None

    async def _execute_task(self, task: Task) -> None:
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            
            print(f"[Orchestrator] Starting task {task.id}: {task.name}")
            
            # Get the handler and execute
            task_type = task.metadata.get("task_type")
            handler = self.task_handlers[task_type]
            
            # Record estimated cost
            if task.estimated_cost > 0:
                category = CostCategory.COMPUTE  # Default category
                if "cost_category" in task.metadata:
                    category = CostCategory(task.metadata["cost_category"])
                
                cost_approved = await self.cost_governor.record_cost(
                    category, task.estimated_cost, f"Task: {task.name}", task.id
                )
                
                if not cost_approved:
                    task.status = TaskStatus.PAUSED
                    task.error_message = "Task paused due to budget constraints"
                    return
            
            # Execute the actual task
            result = await handler(task)
            
            # Update progress in stuck guard
            await self.stuck_guard.update_progress(task.id)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            
            print(f"[Orchestrator] Completed task {task.id}: {task.name}")
            
        except Exception as e:
            task.error_message = str(e)
            task.retry_count += 1
            
            print(f"[Orchestrator] Task {task.id} failed: {e}")
            
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                print(f"[Orchestrator] Will retry task {task.id} ({task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                print(f"[Orchestrator] Task {task.id} failed permanently after {task.retry_count} retries")
        
        finally:
            # Clean up
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            
            # Complete monitoring
            await self.stuck_guard.complete_task(task.id)

    async def _schedule_tasks(self) -> None:
        # Get pending tasks sorted by priority
        pending_tasks = sorted(
            [task for task in self.tasks.values() if task.status == TaskStatus.PENDING],
            key=lambda t: t.priority.value,
            reverse=True
        )
        
        for task in pending_tasks:
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                break
            
            can_start, reason = await self._can_start_task(task)
            if can_start:
                # Start the task
                async_task = asyncio.create_task(self._execute_task(task))
                self.running_tasks[task.id] = async_task
            elif reason and "dependency" not in reason.lower():
                # Log non-dependency issues
                print(f"[Orchestrator] Cannot start task {task.id}: {reason}")

    async def start(self) -> None:
        if self.running:
            print("[Orchestrator] Already running")
            return
        
        self.running = True
        self.shutdown_requested = False
        
        # Start monitoring components
        stuck_guard_task = asyncio.create_task(self.stuck_guard.start_monitoring())
        
        print("[Orchestrator] Started orchestration")
        
        try:
            while self.running and not self.shutdown_requested:
                # Check for stuck tasks
                stuck_tasks = await self.stuck_guard.check_stuck_tasks()
                for task_id in stuck_tasks:
                    if task_id in self.running_tasks:
                        print(f"[Orchestrator] Cancelling stuck task: {task_id}")
                        self.running_tasks[task_id].cancel()
                        if task_id in self.tasks:
                            self.tasks[task_id].status = TaskStatus.FAILED
                            self.tasks[task_id].error_message = "Task cancelled due to timeout"
                
                # Schedule new tasks
                if not self.paused:
                    await self._schedule_tasks()
                
                # Clean up completed async tasks
                completed_task_ids = []
                for task_id, async_task in self.running_tasks.items():
                    if async_task.done():
                        completed_task_ids.append(task_id)
                
                for task_id in completed_task_ids:
                    del self.running_tasks[task_id]
                
                await asyncio.sleep(1)  # Check every second
                
        finally:
            # Stop monitoring
            await self.stuck_guard.stop_monitoring()
            stuck_guard_task.cancel()
            
            # Cancel all running tasks
            for async_task in self.running_tasks.values():
                async_task.cancel()
            
            # Wait for tasks to complete
            if self.running_tasks:
                await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
            
            self.running = False
            print("[Orchestrator] Stopped orchestration")

    async def pause(self) -> None:
        self.paused = True
        print("[Orchestrator] Paused task scheduling")

    async def resume(self) -> None:
        self.paused = False
        print("[Orchestrator] Resumed task scheduling")

    async def shutdown(self) -> None:
        self.shutdown_requested = True
        print("[Orchestrator] Shutdown requested")

    async def cancel_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
        
        task.status = TaskStatus.CANCELLED
        print(f"[Orchestrator] Cancelled task {task_id}")
        return True

    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.value,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "estimated_cost": task.estimated_cost,
            "actual_cost": task.actual_cost,
            "error_message": task.error_message,
            "dependencies": list(task.dependencies),
            "metadata": task.metadata
        }

    def get_system_status(self) -> Dict:
        task_counts = {}
        for status in TaskStatus:
            task_counts[status.value] = len([t for t in self.tasks.values() if t.status == status])
        
        return {
            "running": self.running,
            "paused": self.paused,
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent_tasks,
            "task_counts": task_counts,
            "stuck_guard_status": self.stuck_guard.get_status(),
            "cost_governor_status": self.cost_governor.get_status()
        }


# Example task handlers
async def example_compute_task(task: Task) -> str:
    await asyncio.sleep(2)  # Simulate work
    return f"Computed result for {task.name}"

async def example_api_task(task: Task) -> Dict:
    await asyncio.sleep(1)  # Simulate API call
    return {"api_response": f"Response for {task.name}"}


async def main():
    orchestrator = Orchestrator(max_concurrent_tasks=3)
    
    # Register task handlers
    orchestrator.register_task_handler("compute", example_compute_task)
    orchestrator.register_task_handler("api", example_api_task)
    
    # Create some tasks
    task1_id = await orchestrator.create_task(
        "Process Data", "compute", TaskPriority.HIGH, estimated_cost=5.0
    )
    
    task2_id = await orchestrator.create_task(
        "API Call", "api", TaskPriority.MEDIUM, estimated_cost=2.0
    )
    
    task3_id = await orchestrator.create_task(
        "Final Processing", "compute", TaskPriority.LOW,
        dependencies={task1_id, task2_id}, estimated_cost=3.0
    )
    
    # Start orchestrator
    orchestrator_task = asyncio.create_task(orchestrator.start())
    
    # Let it run for a bit
    await asyncio.sleep(10)
    
    # Check status
    print("\nSystem Status:")
    print(json.dumps(orchestrator.get_system_status(), indent=2))
    
    # Shutdown
    await orchestrator.shutdown()
    await orchestrator_task


if __name__ == "__main__":
    asyncio.run(main())