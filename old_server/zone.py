import asyncio
import json
import operator
from random import choice
from configuration import COLORS, ZoneTransition
from vial import Vial
from configuration import ItemType, ZonePhase,app_data
from vial_manager import vial_manager
from zone_item import ZoneItem
from event_tracker import tasks_auditor

async def execute_after_time(t:int,method ,*args):
    await asyncio.sleep(t)
    method(args)

class Zone:
    
    def __init__(self, data):
        self.zone_id = data['zone_id']
        self.name = data['name']        
        self.subzones = [Zone(subzone) for subzone in data.get('subzones', [])]
        self.zone_items:list[ZoneItem] = [ZoneItem(item,None) for item in data.get('zone_items', [])]
        self.run_time= data.get('run_time', 0)
        self.phase_order = data.get('phase_order', [])
        self.limits_by_color = data.get('limits_by_color', None)
        self.phase= ZonePhase(self.phase_order[0] if self.phase_order else 1)
        self.rows= data.get('rows',0)
        self.columns= data.get('columns',0)
        self.door_opened = False
        self.is_exchange=data.get('is_exchange',False)
        self.sensor_id=data.get('sensor_id',None)
        self.stateful =data.get('stateful',None)
        self.capacity_check=data.get('capacity_check',None)
        self.has_common_door=data.get('has_common_door',False)
        self.zone_stack =data.get('zone_stack')
        self.zone_location =data.get('zone_location')
        self.start_task:asyncio.Task =None

    async def restart(self):
        if self.subzones:
            for subzone in self.subzones: 
                await subzone.restart()
        for item in self.zone_items:
            item.remove_content()
        self.phase= ZonePhase(self.phase_order[0] if self.phase_order else 1)
        self.door_opened =False
        if self.start_task and not self.start_task.done():
            await self.cancel_start_task()

    def get_subzone_by_id(self,id):
        if self.subzones:
            return self.subzones[id-1]

    def get_empty_item(self,position)->ZoneItem:  
        for item in self.zone_items:
            if item.position== position and item.content is None:
                return item
        return None

    def export_data(self,is_gui=False):
        subzones=[]
        if self.subzones:            
            for subzone in self.subzones:
                subzones.append({"zone_id":subzone.zone_id,"zone": subzone.export_data(is_gui)})
        zone_items=[]
        for item in self.zone_items:
            if item.content:
                zone_items.append(item.export_data(is_gui))
        return {"phase":self.phase.value,"zone_items": zone_items,"subzones":subzones}

    def import_data(self,data):
        try: 
            self.phase=ZonePhase(data["phase"])
            zone_items= data["zone_items"]
            for zone_item in zone_items:
                item=self.get_empty_item(zone_item["position"])
                content=json.loads(zone_item["content"])
                
                # DEBUG: Check line_code before Vial creation
                if "line_code" in content:
                    print(f"DEBUG - Before Vial creation: line_code = {content['line_code']} (type: {type(content['line_code'])})")
                
                content=Vial(**content)
                
                # DEBUG: Check line_code after Vial creation
                if hasattr(content, 'line_code'):
                    print(f"DEBUG - After Vial creation: line_code = {content.line_code} (type: {type(content.line_code)})")
                
                item.set_content(content)   
                vial_manager.add_vial(content)
            subzones=data["subzones"]
            if subzones:
                for subzone_obj in subzones:
                    subzone:Zone=self.get_subzone_by_id(subzone_obj["zone_id"])
                    subzone.import_data(subzone_obj["zone"])
        except Exception as e:
            print(e)
    
    
    def get_item_by_line_code(self,barcode):
        for item in self.zone_items:
            if item.content and item.content.line_code == barcode:
                return item
        return None
    
    async def cancel_start_task(self):
        if self.start_task and not self.start_task.done():
            self.start_task.cancel()
            try:
                await self.start_task
            except asyncio.CancelledError as e:
                tasks_auditor.info(f"Task: {self.start_task.get_name()} cancelled successfully.")
