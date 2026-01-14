import json
import os
from typing import Any

import aiofiles
from event_tracker import tasks_auditor,error_auditor

async def write_to_file(data: Any, file_name: str = "zones.json") -> bool:
    try:
        async with aiofiles.open(file_name, 'w') as file: 
            await file.write(json.dumps(data, indent=4)) 
        tasks_auditor.info(
                f"Write: Latest data sent to file: {file_name}")
        return True
    except Exception as e:
        error_auditor.error(f"Error writing to {file_name}: {e}")
        return False


async def read_from_file(file_name: str = "zones.json") -> Any:
    try:
        async with aiofiles.open(file_name, 'r') as file:
            raw_data = await file.read()
        if raw_data:
            data = json.loads(raw_data)                                                         
            tasks_auditor.info(f"Read: Latest data loaded from file: {file_name}")
            return data
        return None
    except Exception as e:
        error_auditor.error(f"Error reading from {file_name}: {e}")
        return None
