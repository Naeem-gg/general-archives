import asyncio
from configuration import COLORS, app_data
from event_tracker import tasks_auditor

async def acquire_zone_lock(lock_id: int, robot_id: int):      
    zone_lock: asyncio.Lock = app_data.zone_locks.setdefault(lock_id, asyncio.Lock())
    await zone_lock.acquire()
    if lock_id != 1:
        tasks_auditor.info(f"Area {lock_id} is locked for Robot:{robot_id}")

async def release_zone_lock(lock_id: int, robot_id: int):
    zone_lock: asyncio.Lock = app_data.zone_locks[lock_id]
    if (zone_lock.locked()):
        zone_lock.release()
    if lock_id != 1:
        tasks_auditor.info(f"Area {lock_id} is released for Robot:{robot_id}")

async def cancel_task(task:asyncio.Task,name="task"):
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError as e:
            tasks_auditor.info(f"Task: {name} cancelled successfully.")
