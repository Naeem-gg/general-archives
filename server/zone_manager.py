import asyncio
from collections import Counter
from datetime import datetime, timedelta,time
from functools import partial
import inspect
from random import choice, randint
from typing import Dict
from data_manager import read_from_file, write_to_file
from futures_manager import futures_manager
from vial import Vial
from zone import Zone
from configuration import COLORS, VIAL_TYPE, ResponseData, ZonePhase, ZoneTransition,ItemType,TaskType,config,app_data,tasks_q,ErrorCodes
from vial_manager import vial_manager
from pallet import get_waypoints
from event_tracker import tasks_auditor,error_auditor
from zone_item import ZoneItem

class ZoneManager:
    
    def __init__(self, config_data):
        self.zones:Dict[int, Zone] = {zone['zone_id']: Zone(zone) for zone in config_data['zones']}
        self.zone_transitions:Dict[int, ZoneTransition]={zone_transition['transition_id']: ZoneTransition(zone_transition) for zone_transition in config_data.get('zone_transitions', [])}
        self.transitions_order_list:Dict[int, list]={transitions_order['transition_order_id']: {k: v for d in transitions_order['transition_orders'] for k, v in d.items()} for transitions_order in config_data.get('transitions_orders', [])}
        self.current_transition_id=0
        self.progress_transition_order()
        self.centri_batch_count=0
        self.xn_batch_count=0
        self.file_loaded=False
        self.camera1_lock = asyncio.Lock()

    def progress_transition_order(self):
        self.current_transition_id =(self.current_transition_id % len(self.transitions_order_list)) +1
        self.transition_order= self.transitions_order_list.get(self.current_transition_id)

    def get_zone(self, zone_id):
        return self.zones.get(zone_id)
    
    def get_transition(self,id):
        return self.zone_transitions.get(id)
    
    async def get_task(self,robot_id):        
        if not tasks_q[robot_id]:
            if self.centri_batch_count ==1:
                self.progress_transition_order()
                self.centri_batch_count=0
            if self.xn_batch_count ==1:
                self.progress_transition_order()
                self.xn_batch_count=0
            if await self.check_capacity(robot_id):
                for transition_id in self.transition_order[robot_id]: 
                    transition=self.get_transition(transition_id)
                    if await self.prepare_task(transition,robot_id):
                        break
        if tasks_q[robot_id]:
            task= tasks_q[robot_id].pop(0)
            tasks_auditor.info(f"Task:{task}")
            return vars(task)
        return vars(ResponseData())
    
    async def get_test_task(self,robot_id): 
        return vars(ResponseData(curr_zone=21, next_zone=0, curr_subzone=21, next_subzone=0, curr_wp={'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}, next_wp={'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}, curr_task=5, next_task=0, item_type=0, vial_type=0, random_id=4680924, color=0, decapped=0, curr_idx=0, next_idx=0))
        return vars(ResponseData(curr_zone=12, next_zone=13, curr_subzone=1, next_subzone=1, curr_wp={'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}, next_wp={'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}, curr_task=2, next_task=1, item_type=2, vial_type=5, random_id=1413435, color=8, decapped=0))
        #return vars(ResponseData(curr_zone=1, next_zone=2, curr_subzone=0, next_subzone=0, curr_wp={'x': 120.0, 'y': 150.0, 'z': 120, 'rx': 120, 'ry': 150, 'rz': 150}, next_wp={'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}, curr_task=2, next_task=1, item_type=1, vial_type=1, random_id=2258972, color=4, decapped=0))
        #return vars(ResponseData(curr_zone=2, next_zone=8, curr_subzone=0, next_subzone=1, curr_wp={'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}, next_wp={'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}, curr_task=2, next_task=1, item_type=1, vial_type=1, random_id=8272704, color=4, decapped=0))
        #return vars(ResponseData(curr_zone=2, next_zone=12, curr_subzone=0, next_subzone=4, curr_wp={'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0}, next_wp={'x': 100.0, 'y': 100.0, 'z': 120, 'rx': 120, 'ry': 150, 'rz': 150}, curr_task=2, next_task=1, item_type=1, vial_type=3, random_id=4162530, color=3, decapped=0))
    async def prepare_task(self,transition:ZoneTransition,robot_id:int):
        if await self.prepare_init_tasks(robot_id):
            return True
        result1=await self.prepare_movement_task(transition,robot_id)
        result2=await self.prepare_stop_task(transition,robot_id)
        result3=await self.prepare_start_task(transition.curr_zone_id,robot_id)
        if result1 or result2 or result3 : return True
        return False
    
    async def prepare_movement_task(self, transition: ZoneTransition,robot_id:int):        
        curr_zone = self.get_zone(transition.curr_zone_id)
        next_zone = self.get_zone(transition.next_zone_id)
        target_zone = self.get_zone(transition.target_zone_id)
        curr_subzone=None
        next_subzone=None 
        curr_item=None       
        if curr_zone is None or next_zone is None: 
            raise "Invalid zone ids configured"
        
        # pre operation to be performed 
        await self.execute_func(transition.pre_operations,transition,curr_subzone or curr_zone,next_subzone or next_zone,robot_id)

        if curr_zone.has_subzones():
            curr_subzone=curr_zone.get_subzone_to_pick(transition)
            if not curr_subzone:
                self.update_possible_next_zone(transition,curr_zone,curr_subzone,curr_item)
                return None
        elif not curr_zone.is_in_phase(transition.curr_phases) or (curr_zone.zone_type is not None and transition.zone_type is not None and curr_zone.zone_type != transition.zone_type): 
            self.update_possible_next_zone(transition,curr_zone,curr_subzone,curr_item)
            return None

        if next_zone.has_subzones():
            next_subzone=next_zone.get_subzone_to_place(transition)
            if not next_subzone : 
                self.update_possible_next_zone(transition,curr_zone,curr_subzone,curr_item)
                return None
        elif not next_zone.is_in_phase(transition.next_phases) or (next_zone.zone_type is not None and transition.zone_type is not None and next_zone.zone_type != transition.zone_type):
            self.update_possible_next_zone(transition,curr_zone,curr_subzone,curr_item)
            return None

        curr_subzone, curr_item = curr_zone.get_subzone_and_item(transition)  
        next_subzone, next_item = next_zone.get_subzone_and_empty_item(transition) 

        if not await self.execute_func(transition.pre_checks,transition,curr_subzone or curr_zone,next_subzone or next_zone,robot_id):            
            return None 
        
        if tasks_q[robot_id]:
            return True
        
        res=self.update_possible_next_zone(transition,curr_zone,curr_subzone,curr_item)
        if res is not None:
            return res

        if transition.item_type == ItemType.VIAL:
            result=False
            if curr_item is None :
                if not transition.possible_next_trans_ids and not transition.orig_trans_ids:
                    if (next_subzone or next_zone).is_loading():
                        if not transition.no_next_phase_change and (target_zone is None or target_zone.is_ready_to_load()):
                            (next_subzone or next_zone).progress_phase()
                            result =True
                return result 
            
            if next_item is None:
                if (not transition.no_next_phase_change or (next_subzone and next_subzone.get_next_empty_item() is None)) and (target_zone is None or target_zone.is_ready_to_load()):
                    (next_subzone or next_zone).progress_phase()
                    result =True
                return result        
        
        random_id= randint(1000000, 9999999)
        curr_type= curr_item.content.type if curr_item and curr_item.content and curr_item.content.type else 1
        color= curr_item.content.color if curr_item and curr_item.content and curr_item.content.color else 0
        decapped =1 if curr_item and curr_item.content and curr_item.content.decapped else 0
        emergency ="Emergency" if curr_item and curr_item.content and curr_item.content.emergency else ''
        line_code =curr_item.content.line_code if curr_item and curr_item.content and curr_item.content.line_code else None
        result = ResponseData(
            curr_zone.zone_id, 
            next_zone.zone_id,
            curr_subzone.zone_id if curr_subzone else 0,
            next_subzone.zone_id if next_subzone else 0,
            get_waypoints(curr_item.position if curr_item else 0,curr_zone.zone_id,curr_subzone.zone_id if curr_subzone else 0, transition.item_type.value,robot_id), 
            get_waypoints(next_item.position if next_item else 0,next_zone.zone_id,next_subzone.zone_id if next_subzone else 0, transition.item_type.value,robot_id), 
            TaskType.UNLOAD.value, 
            TaskType.LOAD.value,
            transition.item_type.value,
            curr_type,
            random_id,
            color,
            decapped,
            curr_idx= curr_item.position if curr_item else 0,
            next_idx= next_item.position if next_item else 0
        )
        curr_subzone= curr_subzone or curr_zone
        next_subzone=next_subzone or next_zone

        if transition.item_type == ItemType.ZONE:
            futures_manager.register_future(random_id,[
            lambda: curr_subzone.move_to_zone(next_zone,next_subzone,transition.item_type),
            lambda: curr_subzone.set_zone_phase(curr_subzone.get_next_phase()),
            lambda: next_subzone.set_zone_phase(next_subzone.get_next_phase()),            
            lambda: tasks_auditor.info(f"Zone moved from {curr_subzone.name} , type: {curr_subzone.zone_type} to {next_subzone.name} , type: {curr_subzone.zone_type},transition_id: {transition.transition_id}"),
            partial(self.execute_post_operations,transition,curr_subzone,next_subzone,robot_id)])
        else:
            futures_manager.register_future(random_id,[
            lambda: tasks_auditor.info(f"Robot:{robot_id} {emergency} Vial code: {line_code}, transit: {curr_item.content.transits[0] if curr_item.content and curr_item.content.transits else None}, color: {COLORS.get(color, f'Color:{color}') if color else None} ,type: {VIAL_TYPE.get(curr_type, f'Type:{curr_type}') if curr_type else ''} moved from {curr_subzone.name} - position: {curr_item.position} to {next_subzone.name} -position: {next_item.position},transition_id: {transition.transition_id}"),
            lambda: curr_item.content and curr_item.content.set_zone(next_zone.zone_id),
            lambda: curr_item.content and curr_item.content.set_subzone(next_subzone.zone_id),
            lambda: curr_item.content and curr_item.content.set_next_zone(None)    , 
            lambda: next_item.set_content(curr_item.content),
            lambda: curr_item.remove_content(),
            lambda: self.update_zone_phases(curr_subzone,next_subzone,transition),
            partial(self.execute_post_operations,transition,curr_subzone,next_subzone,robot_id)
            ])

        # pre tasks like close door /open door 
        await self.execute_func(transition.pre_tasks,transition,curr_subzone or curr_zone,next_subzone or next_zone,robot_id)

        tasks_q[robot_id].append(result)
        return True    
    
    async def prepare_start_task(self,curr_zone_id: int,robot_id:int):
        curr_zone = self.get_zone(curr_zone_id)
        if curr_zone is None: 
            raise ValueError("Invalid zone IDs configured")
        if curr_zone.subzones:
            curr_subzone=curr_zone.get_sub_zone_to_start()
            if curr_subzone is None: return None
        else:
            if  not curr_zone.is_ready_to_start():
                return None
        random_id= randint(1000000, 9999999)
        result = ResponseData(
            curr_zone=curr_zone.zone_id, 
            curr_subzone=curr_subzone.zone_id if curr_subzone else 0,
            curr_task=TaskType.START.value,
            random_id=random_id
            )  
        if curr_zone_id == 21:
            curr_subzone.door_opened =False 
        if curr_zone_id == 8:
            self.update_xn_count(None,None,None,1)
        zone=curr_subzone or curr_zone  
        futures_manager.register_future(random_id,[ 
        partial(curr_subzone.start_zone,curr_zone),
        lambda:curr_subzone.initialize(False),
        lambda: tasks_auditor.info(f"{curr_subzone.name} started.. with {curr_subzone.get_count() } tubes")])
        tasks_q[robot_id].append(result)
        return True
    
    async def prepare_stop_task(self, transition: ZoneTransition,robot_id:int):
        curr_zone = self.get_zone(transition.curr_zone_id)
        if curr_zone is None: 
            raise ValueError("Invalid zone IDs configured")
        if not curr_zone.subzones and not curr_zone.is_ready_to_stop():
            return None
        if curr_zone.subzones:
            for subzone in curr_zone.subzones:
                if subzone.is_ready_to_stop():           
                    if not await self.execute_func(transition.pre_checks,transition,subzone,None,robot_id):            
                        continue         
                    random_id= randint(1000000, 9999999)
                    result = ResponseData(
                        curr_zone=curr_zone.zone_id, 
                        curr_subzone=subzone.zone_id if subzone else 0,
                        curr_task=TaskType.STOP.value,
                        random_id=random_id
                        )  
                    futures_manager.register_future(random_id,[       
                    lambda: subzone.set_zone_phase(subzone.get_next_phase()),
                    lambda:subzone.initialize(False),
                    lambda: tasks_auditor.info(f"{subzone.name} stopped..")])
                    tasks_q[robot_id].append(result)
                    return True
            
        elif curr_zone.is_ready_to_stop():
            if not await self.execute_func(transition.pre_checks,transition,curr_zone,None,robot_id):            
                    return None
            random_id= randint(1000000, 9999999)
            result = ResponseData(
                curr_zone=curr_zone.zone_id, 
                curr_task=TaskType.STOP.value,
                random_id=random_id
                )
            futures_manager.register_future(random_id,[       
            lambda: curr_zone.set_zone_phase(curr_zone.get_next_phase()),
            lambda:curr_zone.initialize(False),
            lambda: tasks_auditor.info(f"{curr_zone.name} stopped..")])
            tasks_q[robot_id].append(result)
            return True
        
    def prepare_doors_task(self, curr_zone:Zone,curr_subzone:Zone,open:bool,robot_id:int):
        random_id= randint(1000000, 9999999)
        result = ResponseData(
            curr_zone=curr_zone.zone_id, 
            curr_subzone=curr_subzone.zone_id if curr_subzone else 0,
            curr_task=TaskType.OPEN.value if open else TaskType.CLOSE.value,
            random_id=random_id
            )
        zone=curr_subzone or curr_zone  
        futures_manager.register_future(random_id,[ 
        lambda:zone.set_door(open),
        lambda: zone.set_zone_phase(zone.get_next_phase()),
        partial(self.export_data,None,None,None,None),
        lambda: tasks_auditor.info(f"{zone.name} Door {"Opened.." if open else "Closed.."} ")])        
        tasks_q[robot_id].append(result)
        return True
    
    def prepare_doors_task_no_progress(self, curr_zone:Zone,curr_subzone:Zone,open:bool,robot_id:int):
        random_id= randint(1000000, 9999999)
        result = ResponseData(
            curr_zone=curr_zone.zone_id, 
            curr_subzone=curr_subzone.zone_id if curr_subzone else 0,
            curr_task=TaskType.OPEN.value if open else TaskType.CLOSE.value,
            random_id=random_id
            )
        zone=curr_subzone or curr_zone  
        futures_manager.register_future(random_id,[ 
        lambda:zone.set_door(open),
        partial(self.export_data,None,None,None,None),
        lambda: tasks_auditor.info(f"{zone.name} Door {"Opened.." if open else "Closed.."} ")])        
        tasks_q[robot_id].append(result)
        return True

    
    async def prepare_pause_task(self, curr_zone:Zone,robot_id:int):
        random_id= randint(1000000, 9999999)
        result = ResponseData(
            curr_zone=curr_zone.zone_id, 
            curr_task=TaskType.PAUSE.value,
            random_id=random_id
            )
        zone=curr_zone  
        futures_manager.register_future(random_id,[
        partial(self.export_data,None,None,None,None)])
        tasks_q[robot_id].append(result)
        return True
    
    # To progreess the zones to next phases
    def update_zone_phases(self,curr_zone:Zone,next_zone:Zone,t:ZoneTransition): 
        target_zone = self.get_zone(t.target_zone_id)    
        #if there is original transition   
        if t.orig_trans_ids:
            for id in t.orig_trans_ids:
                #original transition details
                transition = self.get_transition(id)
                orig_curr_zone= self.get_zone(transition.curr_zone_id)
                orig_curr_subzone, orig_curr_item = orig_curr_zone.get_subzone_and_item(transition)
                orig_curr_subzone=orig_curr_subzone or orig_curr_zone  
                #if loading just started, change phase to LOADING           
                if next_zone.is_loading_started(t):
                    next_zone.progress_phase()
                # if there is no other tube in te current zone.., change the phase
                if curr_zone.get_next_item_transition(t) is None:
                    if not t.no_curr_phase_change:
                        curr_zone.progress_phase()
                if orig_curr_item is not None and not orig_curr_item.content.emergency and next_zone.is_emergency_zone() and (target_zone is None or target_zone.is_ready_to_load()):
                    if not t.no_next_phase_change:
                        next_zone.progress_phase()
                elif orig_curr_item is None and curr_zone.get_next_item_transition(t) is None:
                    #orignal transition also has original transition Ex: exchange 
                    if transition.orig_trans_ids:
                        transition1 = self.get_transition(transition.orig_trans_ids[0])
                        orig_curr_zone1= self.get_zone(transition1.curr_zone_id)
                        orig_curr_subzone1, orig_curr_item1 = orig_curr_zone1.get_subzone_and_item(transition1)
                        zone=orig_curr_subzone1 or orig_curr_zone1
                        if orig_curr_item1 is None:
                            if not transition1.no_curr_phase_change:
                                zone.progress_phase()
                            if (not t.no_next_phase_change or (not next_zone.is_exchange and orig_curr_subzone1 and orig_curr_subzone1.get_next_item() is None)) and (target_zone is None or target_zone.is_ready_to_load()):
                                next_zone.progress_phase()
                    else:
                        if not transition.no_curr_phase_change:
                            orig_curr_subzone.progress_phase()
                        if (not t.no_next_phase_change or (not next_zone.is_exchange and orig_curr_subzone.get_next_item() is None) or next_zone.get_next_empty_item() is None) and (target_zone is None or target_zone.is_ready_to_load()):
                            next_zone.progress_phase()
                elif next_zone.get_next_empty_item_transition(t) is None:
                    if (not t.no_next_phase_change or next_zone.get_next_empty_item() is None) and (target_zone is None or target_zone.is_ready_to_load()):
                        next_zone.progress_phase()
        else:
            if next_zone.is_loading_started(t):
                next_zone.progress_phase()
            if curr_zone.get_next_item_transition(t) is None:
                if not t.no_next_phase_change and (target_zone is None or target_zone.is_ready_to_load()):
                    next_zone.progress_phase()
                if not t.no_curr_phase_change or (not curr_zone.is_exchange and curr_zone.get_next_item() is None):
                    curr_zone.progress_phase()
            elif next_zone.get_next_empty_item_transition(t) is None:
                if not t.no_next_phase_change and (target_zone is None or target_zone.is_ready_to_load()):
                    next_zone.progress_phase()

    def update_possible_next_zone(self,transition: ZoneTransition,curr_zone:Zone,curr_subzone:Zone,curr_item):
        if transition.possible_next_trans_ids:
            result=False
            trans_id = transition.possible_next_trans_ids[0]
            possible_next_transition= self.get_transition(trans_id) 
            if not possible_next_transition : raise "Possible next transitions not configured properly"
            poss_next_zone= self.get_zone(possible_next_transition.next_zone_id)
            poss_next_subzone,poss_next_item =poss_next_zone.get_subzone_and_empty_item(possible_next_transition)
            poss_target_zone= self.get_zone(possible_next_transition.target_zone_id)
            if poss_next_item is None or curr_item is None:
                if (poss_next_subzone or poss_next_zone).is_loading():
                    if (not possible_next_transition.no_next_phase_change and (poss_target_zone is None or poss_target_zone.is_ready_to_load())) or poss_next_subzone.get_next_empty_item() is None:
                        (poss_next_subzone or poss_next_zone).progress_phase()
                        result =True
                if not transition.no_curr_phase_change:
                    (curr_subzone or curr_zone).progress_phase()
                    result =True
                return result
            elif poss_next_item is not None and curr_item is not None and not curr_item.content.is_emergency() and (poss_next_subzone or poss_next_zone).is_emergency_zone():
                if not possible_next_transition.no_next_phase_change and (poss_target_zone is None or poss_target_zone.is_ready_to_load()):
                    (poss_next_subzone or poss_next_zone).progress_phase()
                    result =True
                return result

            
    async def execute_func(self,funcs,transition:ZoneTransition,cuur_zone:Zone,next_zone:Zone,robot_id:int):
        if funcs is None: return True
        for func in funcs:
            func = getattr(self, func, None)
            if not func: return True
            if inspect.iscoroutinefunction(func):
                result= await func(transition,cuur_zone,next_zone,robot_id)
            else:
                result= func(transition,cuur_zone,next_zone,robot_id)
            if not result:
                return result
        return result
    
    async def execute_post_operations(self,transition:ZoneTransition,cuur_zone:Zone,next_zone:Zone,robot_id:int):
        result =True
        if transition.post_operations is None: return True
        for func in transition.post_operations:
            func = getattr(self, func, None)
            if not func: continue
            if inspect.iscoroutinefunction(func):
                result= await func(transition,cuur_zone,next_zone,robot_id)
            else:
                result= func(transition,cuur_zone,next_zone,robot_id)
        return result
    
    async def get_archiv_data(self):
        data = []
        for zone_id in self.zones:
            zone =self.zones[zone_id]
            if zone.stateful:
                data.append({"zone_id":zone_id,"zone": zone.export_data(True)})
        return data
    
    async def get_data(self):
        data = []
        for zone_id in self.zones:
            zone =self.zones[zone_id]
            # names = zone.name
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
        else:
           tasks_auditor.info(f"Vial not found to delete: {barcode}") 

    async def reset_archives(self,zone_id=None):
        dim_archiv_zones=[113,114,115,116]
        if zone_id in dim_archiv_zones:
            for zoneid in dim_archiv_zones:
                zone =self.zones[zoneid]
                if zone:
                    await zone.restart()
        elif zone_id is not None:
            zone =self.zones[zone_id]
            if zone:
                await zone.restart()
        else:
            for zone_id in self.zones:
                zone =self.zones[zone_id]
                if zone.stateful:
                    await zone.restart()
        await self.export_data(None,None,None,1)
        return True
    
    async def reset_empty_archives(self):
        archiv_zones=[112,113,114,115,116]
        for zoneid in archiv_zones:
            zone =self.zones[zoneid]
            if zone and zone.subzones:
                for subzone in zone.subzones: 
                    if subzone.is_in_phase([ZonePhase.READY_TO_UNLOAD]) and subzone.get_count() == 0 and subzone.zone_type not in (1,3):
                        subzone.set_zone_phase(ZonePhase.READAY_TO_PROCESS)                        
        await self.export_data(None,None,None,1)
        return True

    async def reset_fehler(self):
        for zone_id in self.zones:
            zone =self.zones[zone_id]
            if zone.zone_id in (10,101,102):
                await zone.restart()
        return True
                
    # region pre and post operations , pre checks region    
    def set_centrifuged(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        for item in next_zone.zone_items:
            if item.content and item.content.color !=5:
                item.content.set_centrifuged()

    def is_counter_needed(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        count = sum(1 for obj in next_zone.zone_items if obj.content and obj.content.type in transition.types)
        if count % 2 !=0:
            return True 
        if not transition.no_next_phase_change:       
            next_zone.progress_phase()
        if not transition.no_curr_phase_change:       
            curr_zone.progress_phase()
        return False
    
    def prepare_cobas_unload(self,transition:ZoneTransition,cuur_zone:Zone,next_zone:Zone,robot_id:int):
        for item in next_zone.zone_items:
            if item.content is None:  #to be commented               
                item.set_content(Vial(line_code="123456789",color=6,type=item.types[0] if item.types else 2,current_zone_id=transition.next_zone_id,next_zone_id=14,current_subzone_id=next_zone.zone_id)) 
            
    def update_cobas_unload(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        orig_transition=self.get_transition(transition.orig_trans_ids[0])
        orig_curr_zone= self.get_zone(orig_transition.curr_zone_id)
        orig_curr_subzone=orig_curr_zone.get_subzone_to_pick(orig_transition)
        if orig_curr_subzone is None: return
        for vial in vial_manager.vials:
            if vial.current_zone_id == orig_curr_zone.zone_id and vial.current_subzone_id == orig_curr_subzone.zone_id:
                return
        next_zone.progress_phase()

    def change_to_unloading(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        if curr_zone.phase == ZonePhase.READY_TO_UNLOAD:
            curr_zone.progress_phase()

    def check_cobas_unload(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        if any(item.content for item in curr_zone.zone_items):        
            for vial in vial_manager.vials:            
                if vial.current_zone_id == transition.curr_zone_id and vial.current_subzone_id == curr_zone.zone_id and vial.color !=6 :                
                    return True
        for item in curr_zone.zone_items:
            if item.content:
                item.remove_content()
        curr_zone.progress_phase()
        return False
    
    async def init_vial(self,is_present):
        camera2_zone:Zone=self.get_zone(2)
        item=camera2_zone.zone_items[0]
        if is_present:
            vial_manager.add_vial(item.content)
        else:
            item.remove_content()
            camera2_zone.progress_phase()
            tasks_auditor.info(f"tube not found, camera2 phase :{camera2_zone.phase}")
            return

    async def update_camera2_result(self,is_success,type): 
        camera2_zone:Zone=self.get_zone(2)
        item=camera2_zone.zone_items[0]       
        vial = item.content
        if not vial : raise "Invalid operation invoked from robot."
        if not vial.centrifuged:
            vial.type =type       
        if not is_success:      
            vial.next_zone_id =10
            return
        if not vial.centrifuged:
            line_code= item.content.line_code
            vial_manager.validate_line_code(line_code)
            if vial.color  == 10 and vial.line_code != '' and vial.line_code != item.content.line_code:
                vial.next_zone_id = 10
                tasks_auditor.info(f"{vial.line_code} Vial moved to Fehler as it is not matching with {item.content.line_code}")
                return
            vial.line_code= item.content.line_code    
            if vial.color not in (9,10):        
                vial.color= item.content.color
            if not self.is_active_zone(vial.color):
                vial.next_zone_id = 10
                tasks_auditor.info(f"{vial.line_code} Vial moved to Fehler as Machine is not avtive")
                return
            #### without LIS start
            if vial.color in (2,3,8):
                vial.set_transit('DIMM')
            elif vial.color == 4:
                vial.set_transit('SYSM') 
            elif vial.color == 1:
                vial.set_transit('COAG')
            elif vial.color == 9:
                vial.set_transit('BLGR')
            elif vial.color == 10:
                vial.set_transit('ARCH')
        print(vial.blood_bags)
        # if not vial.transits:
        #     vial.line_code= item.content.line_code 
        #     await transit_handler.get_transit(vial.line_code,COLORS[vial.color])
        # is_success= vial.transits and vial.transits[0] is not None and vial.transits[0] !=''
        # if not is_success:
        #     vial.next_zone_id =10
        #     vial.error_code =ErrorCodes.LIS_FAIL
        # await file_mover.run_move_files(is_success,vial.centrifuged,vial.line_code)

    def set_fehler_zone(self,vial:Vial):
        if not vial.centrifuged:                
            vial.color= vial.color
        vial.line_code= vial.line_code
        if not vial.color or vial.color == 0:
            vial.next_zone_id=10 # fehler barcode
            vial.error_code = ErrorCodes.COLOR_FAIL
        elif not vial.line_code or vial.line_code =='':            
            vial.next_zone_id=10 # fehler barcode
            vial.error_code = ErrorCodes.LINE_CODE_FAIL
        else:
            vial.next_zone_id=10 # fehler level
            vial.error_code = ErrorCodes.LEVEL_FAIL

    async def update_camera14_result(self,is_present):
        camera14_zone:Zone=self.get_zone(14)
        item= camera14_zone.zone_items[0]
        if not is_present:
            item.remove_content()
            camera14_zone.progress_phase()
            return
        line_code=item.content.line_code #read_line_code()
        #line_code=item.content.line_code
        vial=vial_manager.get_vial(line_code)
        if not line_code or not vial:
            vial= item.content
            vial.next_zone_id =10 #fehler
            return
        if app_data.app_id == 1005:
            # actual tubes unloaded
            actual_zone_id=vial.current_zone_id
            actual_subzone_id=vial.current_subzone_id
            # virtual tubes unloaded
            virtual_zone:Zone= self.get_zone(item.content.current_zone_id)
            virtual_subzone:Zone= self.get_zone(item.content.current_subzone_id)
            actual_subzone:Zone= self.get_zone(vial.current_subzone_id)
            if item.content.line_code != line_code: #swapping needed            
                # move all items from virtual zone to temporary zone 
                for curr_item in virtual_subzone.zone_items:
                    if curr_item and curr_item.content:
                        curr_item.content.set_zone(1000)
                        curr_item.content.set_subzone(1000)
                        curr_item.remove_content()
                item.content.set_zone(1000)
                item.content.set_subzone(1000)
                item.remove_content()
                # move items from actual zone to the virtual zone
                actual_subzone.move_to_zone(virtual_zone,virtual_subzone,ItemType.VIAL)
                #move all items from temporary zone to actual zone.
                for vial in vial_manager.vials:
                    if vial.current_zone_id == 1000 and vial.current_subzone_id == 1000:
                        vial.set_zone(actual_zone_id)
                        vial.set_subzone(actual_subzone_id)
                        next_item=actual_subzone.get_next_empty_item()
                        next_item.set_content(vial)
                tasks_auditor.info(f"Tubes swapped between {virtual_subzone.name} and {actual_subzone.name}")
            virtual_subzone.progress_phase()               
        item.set_content(vial)  
        return True

    async def restart(self,archiv_reset):
        self.centri_batch_count=0
        self.xn_batch_count=0
        for zone in self.zones:
            await self.zones[zone].restart()
        for transition in self.zone_transitions:
            self.zone_transitions[transition].pick_index = 0 if self.zone_transitions[transition].pick_index else None
            self.zone_transitions[transition].place_index = 0 if self.zone_transitions[transition].place_index else None
        self.init_counter_zone()
        if archiv_reset:
            await self.export_data(None,None,None,1)
            tasks_auditor.info(f"Archive got reset")
        await self.import_data()
        await self.reset_controls()
    
    async def prepare_data(self,results):
        try:
            async with self.camera1_lock:
                camera1Zone:Zone=zone_manager.get_zone(1)
                tasks_auditor.info(f"Camera1 results: {results}")
                for result in results:
                    color=int(result[1])
                    pos=int(result[0])            
                    item_type=camera1Zone.get_item_type(pos)
                    if not item_type:
                        type=self.get_vial_type(color)
                    else:
                        type=item_type
                    emergency_val=camera1Zone.is_emergency_pos(pos)
                    vial=Vial(line_code=str(randint(1000000, 9999999)),color=color,type=type,current_zone_id=1,next_zone_id=2,emergency=emergency_val)
                    camera1Zone.set_item(pos,vial)
                self.display_counts(camera1Zone.zone_items)
        except Exception as e:
            error_auditor.info(f"Error occured in prepare data results: {e}")
    
    async def trigger_camera1(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        if not app_data.cam1_sensor:
            return
        await self.camera_capture()
        app_data.cam1_sensor=False
        return True
    
    async def camera_capture(self):
        if not app_data.cam1_sensor:
            return
        print(f"start: {datetime.now()}")
        #await set_rtde_signal({'id':7,'val':True, 'is_configurable': True})
        #results=await camera1_capture()
        #await set_rtde_signal({'id':7,'val':False, 'is_configurable': True})
        results=[]
        print(f"end: {datetime.now()}")
        if results:
            await self.prepare_data(results)
            print(results)
        app_data.cam1_sensor=False
        return True

    def can_unload_counter(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        for item in curr_zone.zone_items:
            if item.content and item.content.color !=5:
                return False
        if not transition.no_curr_phase_change and all(item.content is None for item in curr_zone.zone_items):
            curr_zone.progress_phase()

        return True
    
    async def check_sensor(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        if curr_zone.sensor_id:
            return app_data.sensors.get(curr_zone.sensor_id, False)
        return True

    def open_door(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        if not curr_zone or not next_zone: return False
        if next_zone.zone_id == 14: #dummy camera2
            archivZone:Zone=zone_manager.get_zone(11) #Archive
            for subzone in archivZone.subzones:
                if subzone.door_opened:
                    return True        
                if subzone.is_in_phase([ZonePhase.PRE_PROCESS]):
                    self.prepare_doors_task(archivZone,subzone,True,robot_id)
                    return True
            return False
        else:
            archivZone:Zone=zone_manager.get_zone(transition.next_zone_id) #Archive
            if next_zone.door_opened:
                return True   
            if next_zone.is_in_phase([ZonePhase.PRE_PROCESS]):
                self.prepare_doors_task(archivZone,next_zone,True,robot_id)
                return True
            return False

    def close_door(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        if curr_zone.zone_id == 14: #dummy camera2
            archivZone: Zone = zone_manager.get_zone(11)  # Archive
        else:
            archivZone:Zone=zone_manager.get_zone(transition.next_zone_id) #Archive

        for subzone in archivZone.subzones:
            # Condition from update_archiv method
            if not subzone.is_in_phase([ZonePhase.READY_TO_UNLOAD]) and subzone.get_next_empty_item() is None:
                if subzone.door_opened:
                    self.prepare_doors_task(archivZone, subzone, False,robot_id)
                subzone.set_zone_phase(ZonePhase.READY_TO_UNLOAD)

            # Condition from close_door method
            elif subzone.is_in_phase([ZonePhase.POST_PROCESS]):
                self.prepare_doors_task(archivZone, subzone, False,robot_id)

    def progress_curr_phase(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        try:
            if curr_zone.get_next_item_transition(transition) is None:
                curr_zone.progress_phase()
        except Exception as e:
            print(e)
    
    def progress_next_phase(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        try:
            if next_zone.get_next_empty_item() is None:
                next_zone.progress_phase()
        except Exception as e:
            print(e)
    
    def progress_next_phase_strictly(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        try:
            next_zone.progress_phase()
        except Exception as e:
            print(e)
    
    def check_items(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        if curr_zone.get_next_item_transition(transition) is None : return False
        if next_zone.get_next_empty_item_transition(transition) is None : return False
        return True

    def open_common_door_curr(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        cobas_archiv_zones= [113,114,115,116]
        sysmex_archiv_zones=[17,18]
        archivZone:Zone=zone_manager.get_zone(transition.curr_zone_id) #Archive
        if transition.curr_zone_id in cobas_archiv_zones: #todo: to be corrected later
            for zone_id in cobas_archiv_zones:
                if transition.curr_zone_id ==zone_id: continue
                zone=self.zones[zone_id]
                if not zone.door_opened:continue
                for subzone in zone.subzones:
                    if subzone.is_in_phase(transition.curr_phases) and next_zone.is_in_phase(transition.next_phases):                        
                        return False
                self.prepare_doors_task(zone,zone,False,robot_id)    
        if transition.curr_zone_id in sysmex_archiv_zones: #todo: to be corrected later
            for zone_id in sysmex_archiv_zones:
                if transition.curr_zone_id ==zone_id: continue
                zone=self.zones[zone_id]
                if not zone.door_opened:continue
                for subzone in zone.subzones:
                    if subzone.is_in_phase(transition.curr_phases) and next_zone.is_in_phase(transition.next_phases):
                        return False
                self.prepare_doors_task(zone,zone,False,robot_id)
        
        if archivZone.door_opened:
            return True
        if transition.curr_phases:
            if not curr_zone.is_in_phase(transition.curr_phases):
                return False

        if transition.next_phases:
            if not next_zone.is_in_phase(transition.next_phases):
                return False

        self.prepare_doors_task(archivZone,archivZone,True,robot_id)
        return True
    
    def open_common_door_next(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        archivZone:Zone=zone_manager.get_zone(transition.next_zone_id) #Archive
        if archivZone.door_opened:
            return True
        if not curr_zone.is_in_phase(transition.curr_phases) or not next_zone.is_in_phase(transition.next_phases):
            return False
        self.prepare_doors_task(archivZone,archivZone,True,robot_id)
        return True
    
    def close_common_door_curr(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        archivZone:Zone=zone_manager.get_zone(transition.curr_zone_id) #Archive
        if not archivZone.door_opened:
            return True
        self.prepare_doors_task(archivZone,archivZone,False,robot_id)
        return True
    
    def close_common_door_next(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        archivZone:Zone=zone_manager.get_zone(transition.next_zone_id) #Archive
        if not archivZone.door_opened:
            return True
        self.prepare_doors_task(archivZone,archivZone,False,robot_id)
        return True

    def open_locks_cobas(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):        
        cobas_zone:Zone=zone_manager.get_zone(transition.curr_zone_id) #Cobas Racks
        if curr_zone.door_opened:
            return True   
        if curr_zone.is_in_phase([ZonePhase.PRE_PROCESS]):
            self.prepare_doors_task(cobas_zone,curr_zone,True,1) # Robot id 1
            return True
        return False
    
    def close_locks_cobas(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):        
        cobas_zone:Zone=zone_manager.get_zone(transition.curr_zone_id) #Cobas Racks
        if not curr_zone.door_opened:
            return False   
        if curr_zone.is_in_phase([ZonePhase.POST_PROCESS]):
            self.prepare_doors_task(cobas_zone,curr_zone,False,1) # Robot id 1
            return False # should be false to just do operation, instead of continue with movement task
        return False    

    def open_locks_cobas_1002(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):        
        cobas_zone:Zone=zone_manager.get_zone(transition.curr_zone_id) #Cobas Racks
        if curr_zone.door_opened:
            return False   
        if curr_zone.is_in_phase([ZonePhase.PRE_PROCESS]):
            self.prepare_doors_task(cobas_zone,curr_zone,True,1) # Robot id 1
            return False
        return False

    async def set_centri_run_time(self):        
        zone:Zone=zone_manager.get_zone(4) #centri zone
        centri_machine=zone.subzones[0]
        centri_machine.run_time= 45
        print(f"Centri run time: {centri_machine.run_time}")
        return True

    def init_counter_zone(self):
        counterZone:Zone=self.get_zone(9)
        counterZone.set_item(1,Vial(line_code="1231",color=5,type=1,current_zone_id=9,next_zone_id=3))
        counterZone.set_item(2,Vial(line_code="1232",color=5,type=2,current_zone_id=9,next_zone_id=3))
        counterZone.set_item(3,Vial(line_code="1233",color=5,type=1,current_zone_id=9,next_zone_id=3))
        counterZone.set_item(4,Vial(line_code="1234",color=5,type=2,current_zone_id=9,next_zone_id=3))

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

    def get_vial_type(self,color):
        for mapping in app_data.color_type_map:
            if color in mapping['colors']:
                return mapping['vial_type']
        return None  # If no mapping found

    async def check_capacity(self,robot_id):
        for zone_id in self.zones:
            zone =self.zones[zone_id]
            if zone.capacity_check:
                if not zone.has_capacity():
                    await self.prepare_pause_task(zone,robot_id)
                    return False
        return True                       

    def can_close_door(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        curr_subzone, curr_item = curr_zone.get_subzone_and_item(transition)  
        next_subzone, next_item = next_zone.get_subzone_and_empty_item(transition)
        if curr_item is None or next_item is None:
            return True
        return False

    def can_open_door(self,transition:ZoneTransition):
        curr_zone = self.get_zone(transition.curr_zone_id)
        next_zone = self.get_zone(transition.next_zone_id)
        curr_subzone, curr_item = curr_zone.get_subzone_and_item(transition)  
        next_subzone, next_item = next_zone.get_subzone_and_empty_item(transition)
        if curr_item is not None and next_item is not None:
            return True
        return False

    def close_door_retest(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        archivZone:Zone=zone_manager.get_zone(transition.curr_zone_id) #Archive
        if archivZone.has_common_door:
            if not archivZone.door_opened:
                return True
            if self.can_close_door(transition,curr_zone,next_zone,robot_id):
                self.prepare_doors_task(archivZone,archivZone,False,robot_id)
            return True
        else:
            if curr_zone.door_opened and not self.check_items(transition,curr_zone,next_zone,robot_id):
                self.prepare_doors_task(archivZone,curr_zone,False,robot_id)
            return True
        
    def close_door_next(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        archivZone:Zone=zone_manager.get_zone(transition.next_zone_id) #Archive
        if next_zone.door_opened and not self.check_items(transition,curr_zone,next_zone,robot_id):
            self.prepare_doors_task(archivZone,next_zone,False,robot_id)
        return True

    def open_door_retest(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        archivZone:Zone=zone_manager.get_zone(transition.curr_zone_id) #Archive
        if archivZone.has_common_door:
            if archivZone.door_opened:
                return True
            if self.can_open_door(transition):
                self.prepare_doors_task(archivZone,archivZone,True,robot_id)
            return True        
        else:
            if not self.check_items(transition,curr_zone,next_zone,robot_id):
                return False
            if curr_zone.door_opened:
                return True        
            self.prepare_doors_task(archivZone,curr_zone,True,robot_id)
            return True    

    def open_door_curr(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        archivZone:Zone=zone_manager.get_zone(transition.curr_zone_id) #Archive
        if archivZone.has_common_door:
            if archivZone.door_opened:
                return True
            if not curr_zone.is_in_phase(transition.curr_phases) or not next_zone.is_in_phase(transition.next_phases):
                return False
            self.prepare_doors_task(archivZone,archivZone,True,robot_id)
            return True
        else:
            for subzone in archivZone.subzones:
                if subzone.is_in_phase(transition.curr_phases):                    
                    if subzone.door_opened:
                        return True        
                    self.prepare_doors_task(archivZone,subzone,True,robot_id)
                    return True
            return False
    
    def open_door_next(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        archivZone:Zone=zone_manager.get_zone(transition.next_zone_id) #Archive
        if archivZone.has_common_door:
            if archivZone.door_opened:
                return True
            if not curr_zone.is_in_phase(transition.curr_phases) or not next_zone.is_in_phase(transition.next_phases):
                return False
            self.prepare_doors_task(archivZone,archivZone,True,robot_id)
            return True
        else:
            for subzone in archivZone.subzones:
                if subzone.is_in_phase([ZonePhase.PRE_PROCESS]):                    
                    if subzone.door_opened:
                        return True        
                    self.prepare_doors_task(archivZone,subzone,True,robot_id)
                    return True
            return False

    def close_all_other_doors(self,archive_zone:Zone,archive_subzone:Zone, robot_id:int):
        for zoneid in self.zones:
            zone = self.zones[zoneid]
            if zone.has_common_door and zone.door_opened and zone.zone_id != archive_zone.zone_id :
                self.prepare_doors_task(zone,zone,False,robot_id)

    def can_close_other_door(self,archive_zone:'Zone',other_zone:'Zone'):
       return other_zone.has_common_door and other_zone.door_opened and other_zone.zone_stack == archive_zone.zone_stack and other_zone.zone_id != archive_zone.zone_id

    def update_centri_count(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        self.centri_batch_count +=1
    
    def update_xn_count(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        self.xn_batch_count +=1

    def close_archive_doors(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        archivZone: Zone = zone_manager.get_zone(11)  # Archive
        for subzone in archivZone.subzones:
            if subzone.door_opened:
                if not subzone.is_in_phase([ZonePhase.POST_PROCESS]):
                    subzone.progress_phase()
                self.prepare_doors_task(archivZone, subzone, False,robot_id)
    
    async def export_errors(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        item=curr_zone.get_next_item()
        next_item=next_zone.get_next_empty_item()
        vial:Vial=item.content if item else None
        if vial:
            data = [
                {
                    'Barcode': vial.line_code,
                    'Farbe': COLORS.get(vial.color, f'Color:{vial.color}') if vial.color else None,
                    'Type': VIAL_TYPE.get(vial.type, f'Type:{vial.type}') if vial.type else None,
                    'Füllstand': vial.fluid_level,
                    'Geräte Code': ', '.join(vial.transits) if vial.transits else "",
                    'Fehler Code': vial.error_code.name if vial.error_code else ErrorCodes.UNKNOWN_FAIL.name,
                    'Fehlermeldung': app_data.error_codes[vial.error_code.name if vial.error_code else ErrorCodes.UNKNOWN_FAIL.name],
                    'Fehlerständer Kategorie' : next_zone.name,
                    'Fehlerständer Position': next_item.position,
                    'Zeit': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        asyncio.create_task(vial_manager.export_errors(data))
    
    async def update_place_index(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        if not curr_zone: return
        zone:Zone=zone_manager.get_zone(transition.curr_zone_id)
        num_subzones = len(zone.subzones)
        curr_index=zone.subzones.index(curr_zone)
        if zone.place_index == curr_index:
            zone.place_index = (zone.place_index +1) % num_subzones
            tasks_auditor.info(f"{zone.name} place index updated to {zone.place_index+1}")
    
    async def update_pick_index(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone,robot_id:int):
        if not next_zone: return
        zone:Zone=zone_manager.get_zone(transition.next_zone_id)
        num_subzones = len(zone.subzones)
        curr_index=zone.subzones.index(next_zone)
        if zone.pick_index == curr_index:
            zone.pick_index = (zone.pick_index +1) % num_subzones
            tasks_auditor.info(f"{zone.name} pick index updated to {zone.pick_index+1}") 

    async def swap_sub_zones(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        camera14_zone:Zone=self.get_zone(14)
        item = camera14_zone.zone_items[0]
        line_code=item.content.line_code 
        line_code=item.content.line_code
        vial=vial_manager.get_vial(line_code)
        if not line_code or not vial:
            vial= item.content
            vial.next_zone_id =10 #fehler
            return     
         # actual tubes unloaded
        actual_zone_id=vial.current_zone_id
        actual_subzone_id=vial.current_subzone_id
        actual_zone =self.get_zone(actual_zone_id)
        actual_subzone:Zone= actual_zone.get_subzone_by_id(actual_subzone_id)
        # virtual tubes unloaded
        virtual_zone:Zone= self.get_zone(transition.curr_zone_id)
        virtual_subzone:Zone= curr_zone #subzone
        if item.content.line_code != vial.line_code: #swapping needed           
            # move all items from virtual zone to temporary zone 
            for curr_item in virtual_subzone.zone_items:
                if curr_item and curr_item.content:
                    curr_item.content.set_zone(1000)
                    curr_item.content.set_subzone(1000)
                    curr_item.remove_content()
            item.content.set_zone(1000)
            item.content.set_subzone(1000)
            item.remove_content()
            # move items from actual zone to the virtual zone
            actual_subzone.move_to_zone(virtual_zone,virtual_subzone,ItemType.VIAL)
            #move all items from temporary zone to actual zone.
            for vial in vial_manager.vials:
                if vial.current_zone_id == 1000 and vial.current_subzone_id == 1000:
                    vial.set_zone(actual_zone_id)
                    vial.set_subzone(actual_subzone_id)
                    next_item=actual_subzone.get_next_empty_item()
                    next_item.set_content(vial)
            tasks_auditor.info(f"Tubes swapped between {virtual_subzone.name} and {actual_subzone.name}")
        virtual_subzone.progress_phase()
        item.set_content(vial)

    def display_counts(self,zone_items):
        colors = [item.content.color for item in zone_items if item.content and item.content.color != 0]
        color_count = Counter(colors)
        output = []
        for color, count in color_count.items():
            if color and color !=0:
                # Ensure color is an integer (it might be a string when loaded from JSON)
                color_key = int(color) if color is not None else None
                if color_key is not None and color_key in COLORS:
                    output.append(f"{COLORS[color_key]}: {count}")
        tasks_auditor.info(" | ".join(output))

    async def retests_exists(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        item=curr_zone.get_next_item_transition(transition)
        if item is None:
            return False
        return True
    
    async def update_emergency(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
         for item in next_zone.zone_items:
            if item.content:
                item.content.emergency = False
    
    async def clear_dustbin(self):
        dustbin=self.get_zone(19) #dust bin
        if dustbin.is_in_phase([ZonePhase.LOADING]):
            for item in dustbin.zone_items:
                if item.content:
                    item.remove_content()
            dustbin.progress_phase()

    async def check_disposal_time(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        #return True
        disposal_time = app_data.disposal_time  # number of days
        if disposal_time:
            added_times = [
                datetime.fromisoformat(item.content.added_time)
                for item in curr_zone.zone_items
                if item.content and item.content.added_time
            ]
            if added_times:
                latest_time = max(added_times)
                if datetime.now() - latest_time > timedelta(days=disposal_time):
                    return True
        return False

    async def check_conrols_time(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        try:
            if app_data.controls_time is None:
                return False
            now = datetime.now()
            controls_time_str =app_data.controls_time
            controls_time = datetime.strptime(controls_time_str, "%H:%M").time()
            c_time_today = datetime.combine(now.date(), controls_time)
            if now >= c_time_today:
                return True
            return False
        except Exception as e:
            return False
    
    async def is_ortho_ready_to_unload(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        ortho_machine_zone: Zone = zone_manager.get_zone(21)  # Ortho Machine
        ortho_machine_subzone=ortho_machine_zone.subzones[0]
        if ortho_machine_subzone.is_ready_to_unload() or ortho_machine_subzone.is_ready_to_stop():
            if ortho_machine_subzone.door_opened:
                return True
            tubes=ortho_machine_subzone.get_count()
            #circles=await ortho_conn.stop()
            circles=tubes
            if tubes!=circles:
                return False 
            self.prepare_doors_task(ortho_machine_zone,ortho_machine_zone,True,robot_id)
            ortho_machine_subzone.rotorNo= 1
            return True
        return False
    
    async def is_ortho_ready_to_unload1(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        ortho_machine_zone: Zone = zone_manager.get_zone(21)  # Ortho Machine
        ortho_machine_subzone=ortho_machine_zone.subzones[0]
        if ortho_machine_subzone.is_ready_to_unload() or ortho_machine_subzone.is_in_phase([ZonePhase.UNLOADING]):
            tubes=ortho_machine_subzone.get_count()
            if tubes == 0:
                return False
            if ortho_machine_subzone.door_opened:
                return True       
            if ortho_machine_subzone.unload_time is not None and ortho_machine_subzone.unload_waiting_time():
                return False     
            #circles=await ortho_conn.stop()
            circles=tubes
            if tubes!=circles:
                return False
            blgr_exists=False
            if ortho_machine_subzone.unload_time is None:
                tasks_auditor.info(f"Ortho Machine screen captures success for unload. Wait timer started for {ortho_machine_subzone.unload_wait_time}")
                for item in ortho_machine_subzone.zone_items:
                    if item.content and item.content.transits[0]=='BLGR':
                        blgr_exists=True
                        break
                if blgr_exists:
                    #await caller.send_voice_ortho("Dies ist eine automatisch generierte Nachricht vom Diabots Labor Roboter: Ich habe eine Immunhämatologie-Probe im Labor Brilon. Bitte überprüfen Sie ob manuelle Arbeiten erforderlich sind. - Ich wiederhole: Ich habe eine Immunhämatologie-Probe im Labor Brilon. Bitte überprüfen Sie ob manuelle Arbeiten erforderlich sind.")                    
                    print()
                for item in ortho_machine_subzone.zone_items:
                    if item and item.content:
                        item.content.progress_transit()

            if ortho_machine_subzone.unload_waiting_time():
                return False
            ortho_machine_subzone.unload_time = None

            retest=False
            for item in ortho_machine_subzone.zone_items:
                if item.content and item.content.color!=10 and item.content.transits[0] not in ('ARCH','ORTH-ARCH'):
                    retest=True
                    break
            if retest:
                ortho_machine_subzone.set_zone_phase(ZonePhase.READY_TO_LOAD)
                await self.set_crosstest_pilots(None,None,ortho_machine_subzone,robot_id)
                self.prepare_doors_task(ortho_machine_zone,ortho_machine_subzone,True,robot_id)
                ortho_machine_subzone.rotorNo= 1
                return False
            else:
                self.prepare_doors_task(ortho_machine_zone,ortho_machine_subzone,True,robot_id)
                ortho_machine_subzone.rotorNo= 1
                return True
        return False
    
    async def reset_zone_type(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        curr_zone.zone_type=None
        return True
    
    async def camera1_pilots_available(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        camera1Zone: Zone = zone_manager.get_zone(1)  # camera1Zone
        #check if emergency tube exists
        for item in camera1Zone.zone_items:
            if item and item.content and item.content.is_emergency():
                return False
        for item in camera1Zone.zone_items:
            if item and item.content and item.content.color == 10:
                return True
        return False
    
    async def progress_transport_archive(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        if (next_zone.get_next_empty_item() is None or not await self.camera1_pilots_available(transition,curr_zone,next_zone,robot_id) )and next_zone.phase == ZonePhase.IN_PROCESS:
            next_zone.progress_phase() # change to Post Process

    async def fill_ortho_archiv(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        if next_zone.get_next_empty_item() is None and next_zone.phase != ZonePhase.READY_TO_UNLOAD:
            next_zone.set_zone_phase(ZonePhase.READY_TO_UNLOAD)

    def cleanup_pilot_racks(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        curr_parent_zone = self.get_zone(transition.curr_zone_id)
        for subzone in curr_parent_zone.subzones:
            if subzone.zone_type == 1 and subzone.phase == ZonePhase.READY_TO_UNLOAD and subzone.get_next_empty_item() is not None: #pilots
                subzone.set_zone_phase(ZonePhase.READAY_TO_PROCESS)    #READY to PROCESS     

    async def calculate_runtime(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        zone_id=transition.next_zone_id        
        count=next_zone.get_count()
        time = None
        if zone_id == 8:
            time= self.get_runtime_xn(count)
        elif zone_id == 6 and next_zone.zone_id == 2:
            time= self.get_runtime_coag(count)
        if time:
            next_zone.run_time=time 
        return False

    def get_runtime_xn(self, tubeCount: int):
        runTime:str=""
        match tubeCount:
            case 1:
                runTime= "5:30"
            case 2:
                runTime= "7:00"
            case 3:
                runTime= "8:00"
            case 4:
                runTime= "9:30"
            case 5:
                runTime= "10:30"
            case 6:
                runTime= "13:00"
            case 7:
                runTime= "13:30"
            case 8:
                runTime= "16:30"
            case 9:
                runTime= "16:30"
            case x if x > 7:
                runTime= "25:00"
        #runTime= "0:30"
        if runTime!="":
            #convert to seconds
            mm, ss = runTime.split(':')
            return int(mm) * 60 + int(ss)
        return None
    
    def get_runtime_coag(self, tubeCount: int):
        runTime:str=""
        match tubeCount:
            case 1:
                runTime= "15:00"
            case 2:
                runTime= "18:00"
            case 3:
                runTime= "20:00"
            case 4:
                runTime= "22:00"
            case 5:
                runTime= "25:00"
            case 6|7:
                runTime= "28:00"
            case 8|9|10:
                runTime= "30:00"
        if tubeCount > 10:
            runTime= "30:40"
        #runTime= "0:30"
        if runTime!="":
            #convert to seconds
            mm, ss = runTime.split(':')
            return int(mm) * 60 + int(ss)
        return None
    
    async def open_door_new(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        if not transition.possible_next_trans_ids:  
            next_zone= self.get_zone(transition.next_zone_id)
            next_subzone =next_zone.get_subzone_to_place(transition)
            if next_subzone is None: return False
            if next_subzone.door_opened:
                return True
            if next_subzone.is_in_phase([ZonePhase.PRE_PROCESS]):
                self.prepare_doors_task(next_zone,next_subzone,True,robot_id)
                return True
            return False
        else:
            trans_id = transition.possible_next_trans_ids[0]
            possible_next_transition= self.get_transition(trans_id) 
            if not possible_next_transition : 
                raise "Possible next transitions not configured properly"
            poss_next_zone= self.get_zone(possible_next_transition.next_zone_id)
            poss_next_subzone =poss_next_zone.get_subzone_to_place(possible_next_transition)
            if poss_next_subzone is None: return False
            if poss_next_subzone.door_opened:
                return True
            if poss_next_subzone.is_in_phase([ZonePhase.PRE_PROCESS]):
                self.prepare_doors_task(poss_next_zone,poss_next_subzone,True,robot_id)
                return True
            return False
        
    async def set_crosstest_pilots(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        CRST="CRST" 
        ortho_archiv_pilot_zone:Zone =self.get_zone(111) #ortho archive pilot zone        
        for item in next_zone.zone_items:
            vial=item.content
            if vial and vial.color == 9 and CRST in vial.transits and vial.blood_bags:
                for bag in vial.blood_bags:
                    if next_zone.get_item_by_line_code(bag) is None: # if not already crst placed in machine
                        pilot=ortho_archiv_pilot_zone.get_item_by_line_code_zone_type(bag,1)
                        if pilot and pilot.content:
                            pilot.content.set_transit(CRST)
    
    async def cross_tests_needed(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id: int):
        CRST = "CRST"
        ortho_archiv_pilot_zone:Zone =self.get_zone(111) #ortho archive pilot zone 
        ortho_machine_zone: Zone = self.get_zone(21).subzones[0]
        transport_archiv= self.get_zone(20)
        if not ortho_machine_zone.is_in_phase([ZonePhase.PRE_PROCESS]):
            return False
        zone_items = ortho_machine_zone.zone_items

        pilots_set = {item.content.line_code for item in zone_items if item.content and item.content.color == 10}

        for item in zone_items:
            vial = item.content
            if vial and vial.color == 9 and CRST in vial.transits and vial.blood_bags:
                # If any blood bag doesn't have a matching color==10 item -> cross test needed
                for bag in vial.blood_bags:
                    if bag not in pilots_set and (ortho_archiv_pilot_zone.get_item_by_line_code_zone_type(bag,1) is not None or transport_archiv.get_item_by_line_code(bag) is not None):
                        return True
        # Either no vial with color==9 or all bags matched correctly            
        if ortho_machine_zone.is_in_phase([ZonePhase.PRE_PROCESS]):
            ortho_machine_zone.progress_phase()
        return False
                
    async def change_transpot_archive(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        if next_zone.phase == ZonePhase.IN_PROCESS:
            next_zone.set_zone_phase(ZonePhase.READY_TO_LOAD) # change to READY_TO_LOAD  dummy or temporary
    
    async def open_ortho_door(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):        
        if curr_zone.get_next_item_transition(transition) is None:
            return False
        ortho_machine_zone: Zone = self.get_zone(21)
        ortho_machine_subzone=ortho_machine_zone.subzones[0]
        if not ortho_machine_subzone.is_active: return False
        if ortho_machine_subzone.is_in_phase([ZonePhase.READY_TO_LOAD,ZonePhase.LOADING]):                    
            if ortho_machine_subzone.door_opened:
                return True   
            # if not await ortho_conn.open_door():
            #     return False     
            self.prepare_doors_task(ortho_machine_zone,ortho_machine_subzone,True,robot_id)
            ortho_machine_subzone.rotorNo= 1
            return True
        return False
    
    async def set_ortho_rotor(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        ortho_machine_zone: Zone = self.get_zone(21)
        ortho_machine_subzone=ortho_machine_zone.subzones[0]
        item:ZoneItem=ortho_machine_subzone.get_next_empty_item_transition(transition)
        rackNo=(item.position - 1) // 4 + 1   
        if ortho_machine_subzone.rotorNo == rackNo:
            return True             
        #while not await ortho_conn.set_rotor(rackNo):
            #await asyncio.sleep(10)
        ortho_machine_subzone.rotorNo= rackNo
        tasks_auditor.info(f"ortho rotor set to {rackNo}")
        return True
    
    async def set_ortho_start(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        ortho_machine_zone: Zone = self.get_zone(21)
        ortho_machine_subzone=ortho_machine_zone.subzones[0]
        transport_archiv :Zone= self.get_zone(20)            
        if next_zone.is_in_phase([ZonePhase.PRE_PROCESS]) and (not await self.cross_tests_needed(None,None,None,1)) or transport_archiv.get_next_item_transition(transition) is None:
            if transport_archiv.is_in_phase([ZonePhase.IN_PROCESS]):
                transport_archiv.progress_phase()
    
    async def set_ortho_start1(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        ortho_machine_zone: Zone = self.get_zone(21)
        ortho_machine_subzone=ortho_machine_zone.subzones[0]
        transport_archiv :Zone= self.get_zone(20)            
        if next_zone.is_in_phase([ZonePhase.PRE_PROCESS]) and (not await self.cross_tests_needed(None,None,None,1)) or transport_archiv.get_next_item_transition(transition) is None:
            if transport_archiv.is_in_phase([ZonePhase.IN_PROCESS]):
                transport_archiv.progress_phase()

    async def set_ortho_rotor_unload(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        ortho_machine_zone: Zone = self.get_zone(21)
        ortho_machine_subzone=ortho_machine_zone.subzones[0]
        item:ZoneItem=ortho_machine_subzone.get_next_item_transition(transition)
        rackNo=(item.position - 1) // 4 + 1
        if ortho_machine_subzone.rotorNo == rackNo:
            return True 
        #while not await ortho_conn.set_rotor(rackNo):
            #await asyncio.sleep(10)
        ortho_machine_subzone.rotorNo= rackNo
        tasks_auditor.info(f"ortho rotor set to {rackNo}")
        await asyncio.sleep(10)
        return True
    
    async def can_dimenstion_stop(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        result=False
        try:
            tasks_auditor.info(f"Dimension screen capture started")
            if curr_zone.zone_id == 1:
                #result=await asyncio.wait_for(dimension1_capture.get_result(),timeout=10)
                result=True
                if result:
                    tasks_auditor.info(f"Dimension screen capture1 success")
                    return True
            elif curr_zone.zone_id == 2:
                #result= await asyncio.wait_for(dimension2_capture.get_result(),timeout=10)
                result=True
                if result:
                    tasks_auditor.info(f"Dimension screen capture2 success")
                    return True
        except asyncio.TimeoutError:
            error_auditor.info(f"Timeout in screen capture Dimension {curr_zone.zone_id}")
        except Exception as e:
            error_auditor.info(f"Exception in screen capture Dimension {curr_zone.zone_id}: {e}")
        tasks_auditor.info(f"Dimension screen capture ended")
        await self.extend_runtime(13,curr_zone.zone_id)
        return False
    
    async def is_curr_zone_active(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        return curr_zone.is_active
    
    async def is_next_zone_active(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        return next_zone.is_active
    
    async def is_not_waiting_period(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        sysmex_zone= self.get_zone(8)
        for subzone in sysmex_zone.subzones:
            if not subzone.is_not_waiting_period():
                return False
        return True

    async def is_ortho_ready_to_load(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        ortho_machine_zone: Zone = zone_manager.get_zone(21)  # Ortho Machine
        ortho_machine_subzone=ortho_machine_zone.subzones[0]
        if not ortho_machine_subzone.is_active:
            return False
        if ortho_machine_subzone.is_in_phase([ZonePhase.READY_TO_LOAD ,ZonePhase.LOADING]):
            if ortho_machine_subzone.door_opened:
                return True      
            self.prepare_doors_task(ortho_machine_zone,ortho_machine_subzone,True,robot_id)
            ortho_machine_subzone.rotorNo= 1
            return True
        return False   

    async def is_controls_zone(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        if not next_zone.is_controls_zone():
            return False
        return self.check_controls_count(curr_zone,transition.next_zone_id)

    async def is_controls_time(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        current_time = datetime.now().time()
        if current_time >= app_data.controls_time:
            return True
        return False

    def check_controls_count(self,curr_zone:Zone,zone_id):        

        # Get rules or safe defaults if zone_id missing
        rules = app_data.zone_controls_map.get(zone_id, {"total": 0, "per_subzone": 0, "transit": None,"mac_zone":0})
        zone = self.get_zone(rules["mac_zone"])

        # Required count based on active subzones
        req_count = rules["per_subzone"] * sum(subzone.is_active and not subzone.controls_processed for subzone in zone.subzones)
        if req_count == 0:
            return False
        # Count items matching the required transit
        rem_count = sum(
            1 for item in curr_zone.zone_items
            if item.content
            and item.content.transits
            and item.content.transits[0] == rules["transit"]
        )
        if rem_count == 0:
            return False
        cnt=(rules["total"] - rem_count)
        return (
            cnt == 0 or cnt < req_count
        )
    def is_controls_available(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        for mapping in app_data.zone_controls_map:
            if self.check_controls_count(curr_zone,mapping):
                return True
        return False  # If no mapping found
     

    async def close_ortho_door(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        ortho_machine_zone: Zone = zone_manager.get_zone(21)  # Ortho Machine
        ortho_machine_subzone=ortho_machine_zone.subzones[0]        
        if ortho_machine_subzone.is_in_phase([ZonePhase.READY_TO_LOAD]):
            if not ortho_machine_subzone.door_opened:
                return True      
            self.prepare_doors_task_no_progress(ortho_machine_zone,ortho_machine_subzone,False,robot_id)
            return True
        if ortho_machine_subzone.is_in_phase([ZonePhase.PRE_PROCESS]) and (not await self.cross_tests_needed(None,None,None,1)):
            return
    #end region

#region test methods    
    
    def check_sensor_test(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        result=True
        return result
    
    def progress_transit_test(self):
        for zone_id in self.zones:
            zone =self.zones[zone_id]
            for item in zone.zone_items:
                vial=item.content
                if vial and vial.transits and vial.transits[0]== "ARCH":
                    if vial.color in (1,3,4,7,8):
                        vial.set_transit(choice(['DXCI','ARCH','ARCH','ARCH','GRABS','SGLAB','EXT3']))
                    elif vial.color == 9:
                        vial.set_transit(choice(['SYSM','ARCH','ARCH','ARCH','GRABS','SGLAB','EXT3'])) 
                    elif vial.color == 10:
                        vial.set_transit(choice(['ACLT','ARCH','ARCH','ARCH','GRABS','SGLAB','EXT3']))
            for subzone in zone.subzones:
                if subzone.phase == ZonePhase.READY_TO_UNLOAD:
                    for item in subzone.zone_items:
                        vial=item.content
                        if vial and vial.transits and vial.transits[0]== "ARCH":
                            if vial.color in (1,3,4,7,8):
                                vial.set_transit(choice(['DXCI','ARCH','ARCH','ARCH','GRABS','SGLAB','EXT3']))
                            elif vial.color == 9:
                                vial.set_transit(choice(['SYSM','ARCH','ARCH','ARCH','GRABS','SGLAB','EXT3'])) 
                            elif vial.color == 10:
                                vial.set_transit(choice(['ACLT','ARCH','ARCH','ARCH','GRABS','SGLAB','EXT3']))

    async def update_camera2_result_test_1002(self,is_success,type): 
        camera2_zone:Zone=self.get_zone(2)
        item=camera2_zone.zone_items[0]       
        vial = item.content
        if not vial : raise "Invalid operation invoked from robot."
        if not type: #todo :comment
            if vial.color in (1,3,7):
                type=1
            elif vial.color in (2,4,8):
                type=2        
        if not vial.centrifuged:
            vial.type =type 
        if not is_success:      
            self.set_fehler_zone(vial)
        if vial.color in (2,3,7,8):
            vial.set_transit('COBA')
        elif vial.color == 4:
            vial.set_transit('SYSM') 
        elif vial.color == 1:
            vial.set_transit('BCSM')
        is_success= vial.transits and vial.transits[0] is not None and vial.transits[0] !=''
        if not is_success:
            vial.next_zone_id =10
            vial.error_code =ErrorCodes.LIS_FAIL
    
    async def update_camera2_result_test_1001(self,is_success,type): 
        camera2_zone:Zone=self.get_zone(2)
        item=camera2_zone.zone_items[0]       
        vial = item.content
        if not vial : raise "Invalid operation invoked from robot."
        if not type and not vial.type: #todo :comment
            if vial.color in (1,4):
                type=1
            elif vial.color in (2,3):
                type=2
        else:
            type =vial.type

        if vial.color in (2,3,7,8):
            if type == 3:
                vial.set_transit('CCOBA')
            else:
                vial.set_transit('COBA')
        elif vial.color == 4:
            if type == 3:
                vial.set_transit('CSYSM')
            else:
                vial.set_transit('SYSM')
        elif vial.color == 1:
            if type == 3:
                vial.set_transit('CCS01')
            else:
                vial.set_transit('CS01')
        if not vial.centrifuged:
            vial.type =type       
        if not is_success:
            vial.next_zone_id=10 # fehler
            vial.color =0
            return
    
    async def update_camera2_result_test_1004(self,is_success,type): 
        camera2_zone:Zone=self.get_zone(2)
        item=camera2_zone.zone_items[0]       
        vial = item.content
        if not vial : raise "Invalid operation invoked from robot."
        if not type: #todo :comment
            if vial.color in (1,3,7):
                type=1
            elif vial.color == 4:
                type=3
            elif vial.color == 2:
                type=2        
        if not vial.centrifuged:
            vial.type =type 
        if not is_success:      
            self.set_fehler_zone(vial)
            return
        if vial.color in (2,3,7):
            vial.set_transit('DXCI')
        elif vial.color == 4:
            vial.set_transit('DXCH') 
        elif vial.color == 1:
            vial.set_transit('ACLT')
        is_success= vial.transits and vial.transits[0] is not None and vial.transits[0] !=''
        if not is_success:
            vial.next_zone_id =10
            vial.error_code =ErrorCodes.LIS_FAIL

    async def update_camera2_result_test_1005(self,is_success,type): 
        camera2_zone:Zone=self.get_zone(2)
        item=camera2_zone.zone_items[0]       
        vial = item.content
        if not vial : raise "Invalid operation invoked from robot."
        if not type: #todo :comment
            if vial.color in (1,3,4):
                type=2
            elif vial.color == 8:
                type=3
            elif vial.color in (7,9,10,2):
                type=1     
        if not vial.centrifuged:
            vial.type =type 
        if not is_success:      
            self.set_fehler_zone(vial)
            return
        if vial.color in (1,2,3,4,7,8):
            vial.set_transit('DXCI')
        elif vial.color == 9:
            vial.set_transit('SYSM') 
        elif vial.color == 10:
            vial.set_transit('ACLT')
        is_success= vial.transits and vial.transits[0] is not None and vial.transits[0] !=''
        if not is_success:
            vial.next_zone_id =10
            vial.error_code =ErrorCodes.LIS_FAIL

    async def update_camera2_result_test_1006(self,is_success,type): 
        camera2_zone:Zone=self.get_zone(2)
        item=camera2_zone.zone_items[0]       
        vial = item.content
        line_code=vial.line_code
        if not vial : raise "Invalid operation invoked from robot."
        if not self.is_active_zone(vial.color):
            vial.next_zone_id = 10
            tasks_auditor.info(f"{vial.line_code} Vial moved to Fehler as Ortho is not avtive")
            return
        if not type: #todo :comment
            if vial.color in (2,8,9):
                type=2
            elif vial.color in (1,4):
                type=1
            elif vial.color == 3:
                type=3   
            elif vial.color == 10:
                type=5
        if not vial.centrifuged:
            vial.type =type 
        if not is_success:      
            self.set_fehler_zone(vial)
            return
        if vial.color in (2,3,8):
            vial.set_transit(choice(['DIMM']))
        elif vial.color == 4:
            vial.set_transit(choice(['SYSM'])) 
        elif vial.color == 1:
            vial.set_transit(choice(['COAG'])) 
        elif vial.color == 10:
            vial.set_transit('ARCH')
        elif vial.color == 9:
            vial.set_transit(choice(['CRST']))
            vial.set_transit(choice(['BLGR']))
            if 'CRST' in vial.transits[0]: 
                for item in self.zones.get(111).subzones[0].zone_items:
                    if item and item.content and 'CRST' not in item.content.transits:
                        vial.blood_bags.append(item.content.line_code)
                        break        
        is_success= vial.transits and vial.transits[0] is not None and vial.transits[0] !=''
        if not is_success and vial.color != 10:
            vial.next_zone_id =10
            vial.error_code =ErrorCodes.LIS_FAIL

    async def test_swap(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):        
        virtual_zone:Zone= self.get_zone(transition.next_zone_id)
        virtual_subzone:Zone= next_zone #subzone
        for zone in virtual_zone.subzones:
            if zone.zone_id!= next_zone.zone_id and  zone.phase == ZonePhase.IN_PROCESS:
                for curr_item in zone.zone_items:
                    if curr_item and curr_item.content:
                        curr_item.content.set_subzone(virtual_subzone.zone_id)
                        curr_item.remove_content()
                for curr_item in virtual_subzone.zone_items:
                    if curr_item and curr_item.content:
                        curr_item.content.set_subzone(zone.zone_id)    
                        curr_item.remove_content()
                for vial in vial_manager.vials:
                    if vial.current_zone_id == transition.next_zone_id and vial.current_subzone_id == virtual_subzone.zone_id:
                        next_item=zone.get_next_empty_item()
                        next_item.set_content(vial)
                        continue
                    if vial.current_zone_id == transition.next_zone_id and vial.current_subzone_id == zone.zone_id:
                        next_item=virtual_subzone.get_next_empty_item()
                        next_item.set_content(vial)
                tasks_auditor.info(f"Samples interchanged between {zone.name} and {virtual_subzone.name}")
                return
    
    async def camera1_exists(self):
        camera1_zone:Zone=self.get_zone(1)   
        return (camera1_zone.get_count() > 0)    
    
    #end region

    async def prepare_init_task(self, curr_zone: Zone,curr_subzone:Zone ,robot_id:int):
        post_tasks=[]
        if curr_zone.zone_id == 8: #for sysmex if job is loading , init is start job only
            if curr_subzone.is_loading():
                curr_subzone.progress_phase()
                return await self.prepare_start_task(8,robot_id)
            elif curr_subzone.is_in_phase([ZonePhase.READY_TO_START,ZonePhase.IN_PROCESS,ZonePhase.READY_TO_STOP]) :
                return False
            else:
                post_tasks= [lambda:curr_subzone.set_door(False),
                             lambda: curr_subzone.set_zone_phase(ZonePhase.PRE_PROCESS)]            
        
        random_id= randint(1000000, 9999999)
        result = ResponseData(
            curr_zone=curr_zone.zone_id, 
            curr_subzone=curr_subzone.zone_id if curr_subzone else 0,
            curr_task=TaskType.INIT.value,
            random_id=random_id
            )   
        zone=curr_subzone or curr_zone  
        post_tasks.append(lambda:zone.initialize())
        futures_manager.register_future(random_id,post_tasks)
        tasks_q[robot_id].append(result)
        return True
    
    async def prepare_init_tasks(self,robot_id):
        cam2_zone=self.zones.get(2)
        #dummy_cam2_zone= self.zones.get(14)
        if cam2_zone.get_count() > 0 :
            return False
        for zone_id in self.zones:
            zone:Zone =self.zones[zone_id]
            if zone.has_subzones():
                for subzone in zone.subzones:
                    if subzone.initialize_needed():
                        return await self.prepare_init_task(zone,subzone,robot_id)
            else:
                if zone.initialize_needed():
                    return await self.prepare_init_task(zone,zone,robot_id)
        return False    
    
    async def add_controls(self):      
        try:
            if app_data.app_id == 1006:
                if not self.file_loaded:
                    return
                archive_zone= self.get_zone(112)
                controls_zone=archive_zone.subzones[3]
                if controls_zone.phase != ZonePhase.READY_TO_UNLOAD:
                    tasks_auditor.info(f"Controls connot be added") 
                    return
                for idx in (1,2,3,4,5,6,11,16,21,26,31,36,41,46):  # covers -8 to -1
                    if idx in (1,2,3,4,5,6): # special case for these positions 
                        vial_type = 2
                        transits = ['DIMM']
                    elif idx in (11,16,21,26,31,36):  # all other positions in range
                        vial_type = 3
                        transits = ['COAG']
                    elif idx in (41,46):  # all other positions in range
                        vial_type = 1
                        transits = ['SYSM']                    
                    vial=Vial(
                            line_code='',
                            color=11,
                            type=vial_type,
                            current_zone_id=112,
                            current_subzone_id=4,
                            next_zone_id=None,
                            transits=transits
                        )
                    item=controls_zone.set_item(idx,vial)
                    item.color=vial.color
                    item.types=[vial.type]
                    vial_manager.add_vial(vial)
                await self.export_data(None,None,None,None) 
                tasks_auditor.info(f"Controls added successfully") 
        except Exception as e:
            print(e)

    async def reset_controls(self):      
        try:
            if app_data.app_id == 1006:
                archive_zone= self.get_zone(112)
                controls_zone=archive_zone.subzones[3]
                for item in controls_zone.zone_items:
                    item.remove_content()
                await self.export_data(None,None,None,None) 
                tasks_auditor.info(f"Controls removed successfully") 
        except Exception as e:
            print(e)

    async def change_device_active(self,id,is_active):
        for zone_id in self.zones:
            zone=self.zones.get(zone_id)
            if zone.change_device_state(id,is_active):
                return True
        return False
    
    def get_zone_by_color(self, color):
        if not isinstance(color, (list, tuple, set)):
            color = [color]

        for mapping in app_data.color_zone_map:
            # Check if any of the input colors match the mapping
            if any(c in mapping['colors'] for c in color):
                return mapping['zone']        
        return None  # No mapping found

    
    def is_active_zone(self,color):
        zone_id= self.get_zone_by_color(color)  
        if zone_id is None:
            return True
        zone:Zone=self.get_zone(zone_id)  
        if zone.is_active_zone():
            return True
        return False
    
    async def send_error_call(self, curr_zone:Zone,curr_subzone:Zone,open:bool,robot_id:int):
        #await caller.send_voice_error("Dies ist eine automatisch generierte Nachricht vom Diabots Labor Roboter: Ich habe ein fehlerhaftes Röhrchen gefunden. Bitte überprüfen Sie die Fehler-Pallette im Labor. - Ich wiederhole: Ich habe ein fehlerhaftes Röhrchen gefunden. Bitte überprüfen Sie die Fehler-Pallette im Labor.")
        print()
    
    async def extend_runtime(self,zone_id,subzone_id):
        zone=zone_manager.get_zone(zone_id)
        subzone:Zone =zone.get_subzone_by_id(subzone_id)
        subzone.set_zone_phase(ZonePhase.READY_TO_START)    

    async def progress_cs_racks_controls(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        if next_zone.get_count() == 3:
            next_zone.progress_phase()

    async def is_transport_free(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        zone=zone_manager.get_zone(20)
        return zone.is_in_phase([ZonePhase.PRE_PROCESS])
    
    async def can_open_archiv(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        archiv_zones =[111,112,113,114,115,116]
        for zone_id in archiv_zones:
            if transition.curr_zone_id != zone_id and transition.next_zone_id !=zone_id:
                zone=self.get_zone(zone_id)
                if zone.door_opened:
                    return False
        return True

    async def set_controls_processed(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        for item in next_zone.zone_items:
            if item.content and item.content.color == 11: #controls
                next_zone.controls_processed=True
                return True
        return False
    
    async def progress_transport(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        if curr_zone.phase == ZonePhase.IN_PROCESS:
            next_zone.progress_phase() # change to Post Process
    
    def set_centrifuged_archiv(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        for item in next_zone.zone_items:
            if item.content:
                item.content.set_centrifuged()

    def set_decapped(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        ca_zone_active= self.get_zone(6).subzones[1].is_active
        if (transition.next_zone_id == 5 and ca_zone_active) or transition.next_zone_id !=5: 
            for item in next_zone.zone_items:
                if item.content:
                    item.content.set_decapped()
    
    def set_added_time(self,transition:ZoneTransition,curr_zone:Zone,next_zone:Zone,robot_id:int):
        for item in next_zone.zone_items:
            if item.content:
                item.content.added_time=datetime.now().isoformat()
    
    async def zone_reset(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        next_zone.set_zone_phase(ZonePhase.READAY_TO_PROCESS)
    
    async def can_pick_vial(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        zone_id= self.get_zone_by_color(transition.colors)  
        now = datetime.now().time()
        if zone_id is None:
            return True
        if zone_id == 8: #sysmex
            start = time(1, 30)
            end = time(2, 35)   
            if start <= now <= end:
                zone=self.get_zone(zone_id)
                for subzone in zone.subzones:
                    if subzone.is_loading():
                        subzone.progress_phase()
                        await self.prepare_start_task(zone_id,robot_id)
                    return False
        elif zone_id in (6,13,21):
            start = time(1, 55)
            end = time(2, 35)
            if start <= now <= end:
                return False
        return True
    
    def is_not_down_time(self, transition: ZoneTransition, curr_zone: Zone, next_zone: Zone, robot_id:int):
        now = datetime.now().time()
        start = time(1, 30)
        end = time(2, 35)   
        test= not (start <= now <= end)
        return test

zone_manager:ZoneManager=ZoneManager(config)  
