import asyncio
from dataclasses import dataclass, field
import inspect
from random import randint
from typing import Callable, Dict, List
from event_tracker import tasks_auditor

@dataclass
class FuturesManager:
    
    futures: Dict[int, List[Callable]] = field(default_factory=dict) 

    def register_future(self,random_id:int, tasks):
        self.futures[random_id] = tasks

    async def execute_future(self, random_id: int):
        if random_id not in self.futures:
            return
        tasks=self.futures[random_id] 
        for task in tasks:
            if not task:
                continue
            if inspect.iscoroutinefunction(task):
                await task() 
            else:
                task()
        tasks_auditor.info(f"Futures completed for random id:{random_id}")
        del self.futures[random_id]

futures_manager = FuturesManager()
