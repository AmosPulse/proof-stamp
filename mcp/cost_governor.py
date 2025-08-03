#!/usr/bin/env python3

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class CostCategory(Enum):
    API_CALLS = "api_calls"
    COMPUTE = "compute"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    MODEL_INFERENCE = "model_inference"


@dataclass
class CostEntry:
    timestamp: float
    category: CostCategory
    amount: float
    description: str
    task_id: Optional[str] = None


@dataclass
class Budget:
    category: CostCategory
    limit: float
    period_seconds: float  # Budget period (e.g., daily = 86400)
    current_usage: float = 0.0
    last_reset: float = 0.0


class CostGovernor:
    def __init__(self, default_budget_limits: Optional[Dict[str, float]] = None):
        self.cost_history: List[CostEntry] = []
        self.budgets: Dict[CostCategory, Budget] = {}
        self.paused_tasks: set = set()
        self.cost_alerts: List[str] = []
        
        # Default budget limits (daily)
        default_limits = default_budget_limits or {
            CostCategory.API_CALLS: 100.0,
            CostCategory.COMPUTE: 50.0,
            CostCategory.STORAGE: 10.0,
            CostCategory.BANDWIDTH: 25.0,
            CostCategory.MODEL_INFERENCE: 200.0
        }
        
        # Initialize budgets with daily periods
        for category, limit in default_limits.items():
            self.set_budget(category, limit, period_seconds=86400)  # 24 hours
        
        print("[CostGovernor] Initialized with default budgets")

    def set_budget(self, category: CostCategory, limit: float, period_seconds: float = 86400) -> None:
        current_time = time.time()
        self.budgets[category] = Budget(
            category=category,
            limit=limit,
            period_seconds=period_seconds,
            current_usage=0.0,
            last_reset=current_time
        )
        print(f"[CostGovernor] Set budget for {category.value}: ${limit:.2f} per {period_seconds/3600:.1f}h")

    def _reset_budget_if_needed(self, category: CostCategory) -> None:
        if category not in self.budgets:
            return
            
        budget = self.budgets[category]
        current_time = time.time()
        
        if current_time - budget.last_reset >= budget.period_seconds:
            budget.current_usage = 0.0
            budget.last_reset = current_time
            print(f"[CostGovernor] Reset budget for {category.value}")

    async def record_cost(self, category: CostCategory, amount: float, 
                         description: str, task_id: Optional[str] = None) -> bool:
        current_time = time.time()
        
        # Reset budget if period has elapsed
        self._reset_budget_if_needed(category)
        
        # Check if adding this cost would exceed budget
        if category in self.budgets:
            budget = self.budgets[category]
            projected_usage = budget.current_usage + amount
            
            if projected_usage > budget.limit:
                alert = f"BUDGET EXCEEDED: {category.value} would cost ${amount:.2f}, " \
                       f"but only ${budget.limit - budget.current_usage:.2f} remaining"
                self.cost_alerts.append(alert)
                print(f"[CostGovernor] {alert}")
                
                if task_id:
                    self.paused_tasks.add(task_id)
                    print(f"[CostGovernor] Paused task {task_id} due to budget constraints")
                
                return False
        
        # Record the cost
        cost_entry = CostEntry(
            timestamp=current_time,
            category=category,
            amount=amount,
            description=description,
            task_id=task_id
        )
        
        self.cost_history.append(cost_entry)
        
        # Update budget usage
        if category in self.budgets:
            self.budgets[category].current_usage += amount
        
        print(f"[CostGovernor] Recorded cost: ${amount:.2f} for {category.value} - {description}")
        
        # Check for warnings (80% of budget)
        if category in self.budgets:
            budget = self.budgets[category]
            usage_percent = (budget.current_usage / budget.limit) * 100
            
            if usage_percent >= 80 and usage_percent < 100:
                warning = f"WARNING: {category.value} at {usage_percent:.1f}% of budget"
                self.cost_alerts.append(warning)
                print(f"[CostGovernor] {warning}")
        
        return True

    async def check_budget_status(self, category: CostCategory) -> Dict:
        if category not in self.budgets:
            return {"error": f"No budget set for {category.value}"}
        
        self._reset_budget_if_needed(category)
        budget = self.budgets[category]
        
        return {
            "category": category.value,
            "limit": budget.limit,
            "current_usage": budget.current_usage,
            "remaining": budget.limit - budget.current_usage,
            "usage_percent": (budget.current_usage / budget.limit) * 100,
            "period_hours": budget.period_seconds / 3600,
            "time_until_reset": budget.period_seconds - (time.time() - budget.last_reset)
        }

    async def get_total_costs(self, category: Optional[CostCategory] = None, 
                            hours_back: Optional[float] = None) -> float:
        current_time = time.time()
        cutoff_time = current_time - (hours_back * 3600) if hours_back else 0
        
        total = 0.0
        for entry in self.cost_history:
            if entry.timestamp >= cutoff_time:
                if category is None or entry.category == category:
                    total += entry.amount
        
        return total

    async def get_cost_breakdown(self, hours_back: float = 24.0) -> Dict[str, float]:
        current_time = time.time()
        cutoff_time = current_time - (hours_back * 3600)
        
        breakdown = {category.value: 0.0 for category in CostCategory}
        
        for entry in self.cost_history:
            if entry.timestamp >= cutoff_time:
                breakdown[entry.category.value] += entry.amount
        
        return breakdown

    async def pause_task(self, task_id: str, reason: str) -> None:
        self.paused_tasks.add(task_id)
        alert = f"Task {task_id} paused: {reason}"
        self.cost_alerts.append(alert)
        print(f"[CostGovernor] {alert}")

    async def resume_task(self, task_id: str) -> bool:
        if task_id in self.paused_tasks:
            self.paused_tasks.remove(task_id)
            print(f"[CostGovernor] Resumed task {task_id}")
            return True
        return False

    async def is_task_paused(self, task_id: str) -> bool:
        return task_id in self.paused_tasks

    def get_status(self) -> Dict:
        status = {
            "total_costs_24h": 0.0,
            "paused_tasks": list(self.paused_tasks),
            "recent_alerts": self.cost_alerts[-10:],  # Last 10 alerts
            "budgets": {}
        }
        
        # Calculate total costs for last 24 hours
        current_time = time.time()
        cutoff_time = current_time - (24 * 3600)
        
        for entry in self.cost_history:
            if entry.timestamp >= cutoff_time:
                status["total_costs_24h"] += entry.amount
        
        # Add budget status
        for category, budget in self.budgets.items():
            self._reset_budget_if_needed(category)
            status["budgets"][category.value] = {
                "limit": budget.limit,
                "used": budget.current_usage,
                "remaining": budget.limit - budget.current_usage,
                "usage_percent": (budget.current_usage / budget.limit) * 100
            }
        
        return status

    async def export_cost_report(self, hours_back: float = 24.0) -> str:
        current_time = time.time()
        cutoff_time = current_time - (hours_back * 3600)
        
        report_data = {
            "report_generated": current_time,
            "period_hours": hours_back,
            "total_cost": await self.get_total_costs(hours_back=hours_back),
            "cost_breakdown": await self.get_cost_breakdown(hours_back),
            "budget_status": {
                category.value: await self.check_budget_status(category)
                for category in self.budgets.keys()
            },
            "cost_entries": [
                {
                    "timestamp": entry.timestamp,
                    "category": entry.category.value,
                    "amount": entry.amount,
                    "description": entry.description,
                    "task_id": entry.task_id
                }
                for entry in self.cost_history
                if entry.timestamp >= cutoff_time
            ]
        }
        
        return json.dumps(report_data, indent=2)


async def main():
    governor = CostGovernor()
    
    # Simulate some API costs
    await governor.record_cost(CostCategory.API_CALLS, 5.50, "GPT-4 API call", "task_1")
    await governor.record_cost(CostCategory.COMPUTE, 12.25, "Model training", "task_2")
    await governor.record_cost(CostCategory.MODEL_INFERENCE, 8.75, "Text generation")
    
    # Check status
    print("\nStatus:", json.dumps(governor.get_status(), indent=2))
    
    # Export report
    report = await governor.export_cost_report(hours_back=1.0)
    print("\nCost Report:")
    print(report)


if __name__ == "__main__":
    asyncio.run(main())