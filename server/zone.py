import asyncio
from datetime import datetime, timedelta
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
        self.pick_index =data.get('pick_index',0)
        self.place_index =data.get('place_index',0)
        self.zone_type =data.get('zone_type',None)
        self.pallets= data.get('pallets',0)
        self.is_active = bool(data.get('is_active', True))
        self.stand_by_time = data.get('stand_by_time',None)
        self.wait_time = data.get('wait_time',None)
        self.last_init_time =None
        self.gui_id = data.get('gui_id',None)
        self.unload_wait_time =data.get('unload_wait_time',0)
        self.unload_time =None
        self.controls_processed =False
        self.rotorNo=1

    def get_subzone_by_id(self,id):
        if self.subzones:
            return self.subzones[id-1]
    
    def get_limits_by_color(self,limits):
        if not limits: return None  
        return {color: limit for color, limit in limits}

    def get_next_empty_item(self)->ZoneItem:  
        for item in self.zone_items:
            if item.content is None:
                return item
        return None
    
    def get_empty_item(self,position)->ZoneItem:  
        for item in self.zone_items:
            if item.position== position and item.content is None:
                return item
        return None

    def get_item_type(self,position)->ZoneItem:        
        type = self.zone_items[position-1].types
        return type[0] if type else None

    def set_item(self,pos:int,content:'Vial'):
        item:ZoneItem=next((i for i in self.zone_items if i.position == pos), None)
        item.set_content(content)
        return item

    def get_next_item(self):
        for item in self.zone_items:
            if item.content is not None:
                return item
        return None    
    
    def set_zone_phase(self,phase:ZonePhase):
        p=self.phase
        if isinstance(phase,tuple):
            self.phase=phase[0]
        else:
            self.phase=phase
        #if self.name != "Camera1" and self.name != "Camera2" and self.name != "Dummy Camera2":
        tasks_auditor.info(f"{self.name} changed from {p} to {self.phase}")
    
    def get_zone_phase(self):
        return self.phase
    
    def get_next_phase(self):
        try:
            index = self.phase_order.index(self.phase.value)
            if index + 1 < len(self.phase_order):
                return ZonePhase(self.phase_order[index + 1])
            else:
                return self.phase  
        except ValueError:
            return self.phase
    
    def is_ready_to_start(self):
        if len(self.subzones)>0:
            for zone in self.subzones:
                if zone.is_ready_to_start():
                    return True
            return False        
        else:
            return self.phase == ZonePhase.READY_TO_START 
    
    def is_ready_to_stop(self):
        if len(self.subzones)>0:
            for zone in self.subzones:
                if zone.is_ready_to_stop():
                    return True
            return False        
        else:
            return self.phase == ZonePhase.READY_TO_STOP
    
    def is_ready_to_load(self):
        if len(self.subzones)>0:
            for zone in self.subzones:
                if zone.is_ready_to_load() and zone.is_active:
                    return True
            return False        
        else:
            return self.phase == ZonePhase.READY_TO_LOAD
        
    async def start_zone(self,zone):
        if len(self.subzones)>0:
            for zone in self.subzones:
                if zone.is_ready_to_start():
                    await zone.start_zone(zone)
                    return
        else: 
            self.set_zone_phase(self.get_next_phase())
            if(self.run_time>0):
                phase=self.get_next_phase()
                await self.cancel_start_task()
                self.start_task=asyncio.create_task(execute_after_time(self.run_time, self.set_zone_phase,phase))
                self.start_call_backs(zone)

    def stop_zone(self):
        if len(self.subzones)>0:
            for zone in self.subzones:
                if zone.is_ready_to_stop():
                    zone.stop_zone()
                    return
        else:        
            self.set_zone_phase(self.get_next_phase())     
    
    def move_to_zone(self,next_zone:'Zone',next_sub_zone:'Zone',item_type:ItemType):
        for curr_item in self.zone_items:
            if curr_item and curr_item.content:
                curr_item.content.set_zone(next_zone.zone_id)
                curr_item.content.set_subzone(next_sub_zone.zone_id)
                next_item=next_sub_zone.get_empty_item(curr_item.position)
                next_item.set_content(curr_item.content)
                curr_item.remove_content() 
        if self.zone_type:
            (next_sub_zone or next_zone).zone_type = self.zone_type
    
    def get_sub_zone_to_start(self):
        return next((subzone for subzone in self.subzones if subzone.phase == ZonePhase.READY_TO_START), None)
    
    def get_sub_zone_to_stop(self):
        return next((subzone for subzone in self.subzones if subzone.phase == ZonePhase.READY_TO_STOP), None) 
       
    def get_subzone(self, phases):
        for phase in phases:
            subzone = next((subzone for subzone in self.subzones if subzone.phase == phase), None)
            if subzone:
                return subzone
        return None

    def get_subzone_to_pick(self, transition:ZoneTransition):
        num_subzones = len(self.subzones)
        # Step 1: Pick emergency subzone first, if any
        for phase in transition.curr_phases:
            subzone = next((subzone for subzone in self.subzones if subzone.phase == phase and subzone.is_emergency_zone()), None)
            if subzone:
                return subzone        
        for phase in transition.curr_phases:
            for i in range(num_subzones):
                index=(self.pick_index + i) % num_subzones
                subzone = self.subzones[index]
                if subzone.phase == phase and (subzone.zone_type is None or transition.zone_type is None or subzone.zone_type == transition.zone_type):
                    return subzone
        if not transition.curr_phases:
            subzone = next((subzone for subzone in self.subzones if subzone.get_next_item_transition(transition,subzone.is_emergency_zone()) is not None 
                            and (subzone.zone_type is None or transition.zone_type is None or subzone.zone_type == transition.zone_type)), None)
            if subzone:
                return subzone
        return None
    
    def get_subzone_to_place(self, transition: ZoneTransition):
        num_subzones = len(self.subzones)
        if transition.control_process_check:
            for phase in transition.next_phases:
                subzone = next((subzone for subzone in self.subzones if subzone.phase == phase and subzone.is_active and  not subzone.controls_processed), None)
                if subzone:
                    return subzone
            return None
        for phase in transition.next_phases:  
            for i in range(num_subzones):    
                index = (self.place_index + i) % num_subzones
                subzone = self.subzones[index]
                if subzone.phase == phase and subzone.is_active and (subzone.zone_type is None or transition.zone_type is None or subzone.zone_type == transition.zone_type):
                    return subzone
        return None
    
    def get_subzone_and_item(self, transition:ZoneTransition):
        subzone=None
        if self.subzones:
            subzone = self.get_subzone_to_pick(transition)
            if not subzone : return None,None  
        zone= subzone or self
        item = zone.get_next_item_transition(transition,zone.is_emergency_zone())
        return subzone, item
    
    def get_subzone_and_empty_item(self, transition:ZoneTransition):
        subzone=None
        if self.subzones:
            subzone = self.get_subzone_to_place(transition)
            if not subzone : return None,None  
        else:
            if not self.is_in_phase(transition.next_phases):
                return None,None
            if not (self.zone_type is None or transition.zone_type is None or self.zone_type == transition.zone_type):
                return None,None
        if (subzone or self).color_limit_exceeded(transition.colors): 
            return subzone,None          
        item = (subzone or self).get_next_empty_item_transition(transition)
        return subzone, item
    
    def get_sorted(self,prop=None)-> list[ZoneItem]:
        if prop:
            return sorted(self.zone_items, key=operator.attrgetter(prop))
        else:
            return self.zone_items
        
    def get_next_item_transition(self,transition:'ZoneTransition',emergency=False):
        items=self.get_sorted(transition.curr_order_by)     
        #for emergency
        for item in items:
            if item and item.content and item.content.is_emergency():
                if item.content.matches(transition):
                    return item   
        if emergency:
            return  None
        if transition.pick_index:
            total_items = len(items)
            for i in range(total_items):
                index = (transition.pick_index + i) % total_items
                item:ZoneItem=items[index]
                if item and item.content is not None and item.content.matches(transition):
                    transition.pick_index = index
                    return items[index]
        else:
            for item in items:
                if item.content is not None and item.content.matches(transition) :
                    return item
        return None
    
    def get_next_empty_item_transition(self,transition:'ZoneTransition'):
        items=self.zone_items
        if transition.place_index:
            total_items = len(items)
            for i in range(total_items):
                index = (transition.place_index + i) % total_items
                item:ZoneItem=items[index]
                if item and item.content is None and item.matches(transition) and not self.color_limit_exceeded(transition.colors):
                    transition.place_index = index 
                    return items[index]
        else:
            for item in items:
                if item.content is None and item.matches(transition) and not self.color_limit_exceeded(transition.colors):
                    return item
        return None
    
    def color_limit_exceeded(self, colors):
        if not colors or not self.limits_by_color:
            return False

        # Count how many items in the zone match the given color IDs
        color_count = {}
        for obj in self.zone_items:
            if obj.content and obj.content.color in colors:
                color_id = obj.content.color
                color_count[color_id] = color_count.get(color_id, 0) + 1

        if not color_count:
            return False

        # Check limits, supporting single integer or list of integers
        for item in self.limits_by_color:
            item_colors = item['color']
            if isinstance(item_colors, int):  # convert single int to list
                item_colors = [item_colors]

            total_for_group = sum(color_count.get(color_id, 0) for color_id in item_colors)
            if total_for_group >= item['limit']:
                return True

        return False


    
    def is_loading_started(self,t:ZoneTransition):
        if self.phase != ZonePhase.READY_TO_LOAD:
            return False
        count = sum(1 for obj in self.zone_items if obj.content) 
        return count == 1
    
    def progress_phase(self):
        try:
            self.set_zone_phase(self.get_next_phase())
        except Exception as e:
            print(e)
    
    def is_loading(self):
        if self.phase != ZonePhase.LOADING:
            return False
        count = sum(1 for obj in self.zone_items if obj.content) 
        return count >= 1
    
    def has_subzones(self):
        return len(self.subzones)>0
    
    def is_in_phase(self,phases):
        return self.phase in phases
    
    def set_door(self,open:bool):
        self.door_opened =open
    
    def set_door_close(self):
        self.door_opened =False	
    
    def get_count(self):
        return sum(1 for obj in self.zone_items if obj.content)

    async def restart(self):
        if self.subzones:
            for subzone in self.subzones: 
                await subzone.restart()
        for item in self.zone_items:
            item.remove_content()
        self.phase= ZonePhase(self.phase_order[0] if self.phase_order else 1)
        self.door_opened =False
        self.pick_index=0
        self.place_index=0
        self.last_init_time=None
        self.unload_time=None
        if self.start_task and not self.start_task.done():
            await self.cancel_start_task()

    def start_call_backs(self,zone:'Zone'):
        if app_data.app_id in (1002,1005,1006): 
            if zone.zone_id in (6,8,13,21):
                for item in self.zone_items:
                    vial=item.content
                    if vial: 
                        if vial.centrifuged:                       
                            vial.set_decapped() 
                        if zone.zone_id !=21:               
                            vial.progress_transit()                        

    def export_data(self,is_gui=False):
        subzones=[]
        if self.subzones:            
            for subzone in self.subzones:
                subzones.append({"zone_id":subzone.zone_id,"zone": subzone.export_data(is_gui)})
        zone_items=[]
        for item in self.zone_items:
            if item.content:
                zone_items.append(item.export_data(is_gui))
        return {"phase":self.phase.value,"zone_items": zone_items,"subzones":subzones,"door_opened": self.door_opened, "zone_type": self.zone_type,"zone_name":self.name}

    def import_data(self,data):
        try:
            self.phase=ZonePhase(data["phase"])
            self.zone_type = data.get("zone_type", self.zone_type)
            if self.stateful:
                self.door_opened =bool(data["door_opened"] if 'door_opened' in data else False)
            zone_items= data["zone_items"]
            if self.zone_id == 20:
                if self.phase == ZonePhase.IN_PROCESS:
                    self.progress_phase()
            for zone_item in zone_items:
                item=self.get_empty_item(zone_item["position"])
                content=json.loads(zone_item["content"])
                content=Vial(**content)
                item.set_content(content)   
                vial_manager.add_vial(content)
            subzones=data["subzones"]
            if subzones:
                for subzone_obj in subzones:
                    subzone:Zone=self.get_subzone_by_id(subzone_obj["zone_id"])
                    subzone.import_data(subzone_obj["zone"])
        except Exception as e:
            print(e)

    def has_capacity(self):
        if self.subzones:            
            for subzone in self.subzones:
                if subzone.zone_type and subzone.zone_type not in (1,3) and subzone.get_next_empty_item():
                    return True
        else:
            if self.get_next_empty_item():
                return True
        return False

    async def cancel_start_task(self):
        if self.start_task and not self.start_task.done():
            self.start_task.cancel()
            try:
                await self.start_task
            except asyncio.CancelledError as e:
                tasks_auditor.info(f"Task: {self.start_task.get_name()} cancelled successfully.")
                
    def get_item_by_line_code(self,barcode):
        if self.subzones:
            for subzone in self.subzones:
                item= subzone.get_item_by_line_code(barcode)
                if item:
                    return item
        else:
            for item in self.zone_items:
                if item.content and item.content.line_code == barcode:
                    return item
        return None
    
    def is_emergency_zone(self):
        for item in self.zone_items:
            if item.content and item.content.is_emergency():
                return True
        return False
    
    def is_emergency_pos(self,position)->bool:        
        item:ZoneItem= self.zone_items[position-1]
        return item.emergency
    
    def is_ready_to_unload(self):
        if len(self.subzones)>0:
            for zone in self.subzones:
                if zone.is_ready_to_unload():
                    return True
            return False        
        else:
            return self.phase == ZonePhase.READY_TO_UNLOAD
    
    def initialize(self,wait_time=True): # wait time flag to decide if we need wait time or not
        if self.stand_by_time:
            if not wait_time:
                self.last_init_time = datetime.now() - timedelta(seconds=self.wait_time)     
            else:
                self.last_init_time =datetime.now()    
            tasks_auditor.info(f"{self.name} initialized..")

    def initialize_needed(self):
        if not self.stand_by_time or not self.is_active:
            return False
        return self.last_init_time is None or ((datetime.now() - self.last_init_time).total_seconds() > self.stand_by_time)

    def is_not_waiting_period(self):
        if self.last_init_time is None:
            return True
        if self.last_init_time and ((datetime.now() - self.last_init_time).total_seconds() > self.wait_time):
            return True
        return False
    
    def is_controls_zone(self):
        if self.get_count() == 0: return True
        if self.zone_id == 17: return True
        if self.get_count() >=3 : return False
        for item in self.zone_items:
            if item.content and item.content.color == 11: #controls
                return True
        return False
    
    def is_controls_exist(self):
        for item in self.zone_items:
            if item.content and item.content.color == 11: #controls
                return True
        return False
    
    def can_place_controls(self):
        for item in self.zone_items:
            if item.color == 11: #controls
                return True
        return False  
    
    def change_device_state(self,id,is_active):
        if self.subzones:            
            for subzone in self.subzones:
                subzone.change_device_state(id,is_active)
        else:
            if self.gui_id == id:
                self.is_active = is_active
                tasks_auditor.info(f"Device {self.name} made avtive: {is_active} ")
                return True
        return  False
    
    def is_active_zone(self):
        if self.subzones:            
            for subzone in self.subzones:
                if subzone.is_active:
                    return True
        else:
            if self.is_active:                
                return True
        return  False
    
    def unload_waiting_time(self):
        if self.unload_time is None:
            self.unload_time =datetime.now()
            return True
        if self.unload_time and ((datetime.now() - self.unload_time).total_seconds() < self.unload_wait_time):
            return True
        return False
    
    def get_item_by_line_code_zone_type(self,barcode,zone_type=None):
        if self.subzones:
            for subzone in self.subzones:
                if zone_type is None or subzone.zone_type is None or  subzone.zone_type == zone_type:
                    item= subzone.get_item_by_line_code_zone_type(barcode,zone_type)
                    if item:
                        return item
        else:
            if zone_type is None  or self.zone_type is None or  self.zone_type == zone_type:
                for item in self.zone_items:
                    if item.content and item.content.line_code == barcode:
                        return item
        return None
