import asyncio
from functools import partial
import inspect
from random import choice, randint
from typing import Dict
from data_manager import read_from_file, write_to_file
from vial import Vial
from zone import Zone
from configuration import COLORS, VIAL_TYPE, ResponseData, ZonePhase, ZoneTransition,ItemType,TaskType,config,app_data,tasks_q
from vial_manager import vial_manager
from event_tracker import tasks_auditor

class ZoneManager:
    
    def __init__(self, config_data):
        self.zones:Dict[int, Zone] = {zone['zone_id']: Zone(zone) for zone in config_data['zones']}
        self.zone_transitions:Dict[int, ZoneTransition]={zone_transition['transition_id']: ZoneTransition(zone_transition) for zone_transition in config_data.get('zone_transitions', [])}

    def get_zone(self, zone_id):
        return self.zones.get(zone_id)
    
    async def restart(self,archiv_reset):
        for zone in self.zones:
            await self.zones[zone].restart()
        if archiv_reset:
            await self.export_data(None,None,None,1)
            tasks_auditor.info(f"Archive got reset")
        await self.import_data()
        print(self.zones)

    async def export_data(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        data = []
        for zone_id in self.zones:
            zone =self.zones[zone_id]
            if zone.stateful:
                data.append({"zone_id":zone_id,"zone": zone.export_data()})
        await write_to_file(data) 
    
    async def import_data(self):
        data=await read_from_file()
        if data:
            for zone_data in data:
                zone_id=zone_data["zone_id"]
                zone=self.get_zone(zone_id)
                zone.import_data(zone_data["zone"])
                
    async def get_archiv_data(self):
        data = []
        for zone_id in self.zones:
            zone =self.zones[zone_id]
            if zone.stateful:
                data.append({"zone_id":zone_id,"zone": zone.export_data(True)})
        return data
    
    async def delete_vial_by_barcode(self,barcode):
        vial=vial_manager.get_vial(barcode)
        if vial:
            curr_zone=self.get_zone(vial.current_zone_id)
            curr_subzone:Zone=curr_zone.get_subzone_by_id(vial.current_subzone_id)
            item=(curr_subzone or curr_zone).get_item_by_line_code(barcode)
            if item:
                item.remove_content()
                vial_manager.delete_vial(vial)
                tasks_auditor.info(f"Vial {vial.line_code} removed via GUI from zone: {vial.current_zone_id},sub_zone: {vial.current_subzone_id}, position: {item.position}")
                await self.export_data(None,None,None,1)

zone_manager:ZoneManager=ZoneManager(config)  
