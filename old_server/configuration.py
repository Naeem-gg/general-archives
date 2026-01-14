import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List
import yaml

def load_yaml():
    with open('zones_config.yaml', 'r') as file:
        return yaml.safe_load(file)

config= load_yaml()
COLORS={}
ROBOTS={}
TRANSITS=[]
ZONE_PHASE ={}
VIAL_TYPE ={}
tasks_q={}

class TaskType(Enum):
    LOAD = 1
    UNLOAD = 2
    START = 3
    STOP = 4
    OPEN = 5
    CLOSE =6
    PAUSE= 7

class ItemType(Enum):
    VIAL = 1
    ZONE = 2

class ZonePhase(Enum):
    READY_TO_LOAD = 1
    READY_TO_START = 2
    IN_PROCESS = 3
    READY_TO_STOP = 4
    READY_TO_UNLOAD = 5
    READAY_TO_PROCESS = 6
    LOADING=7
    UNLOADING=8
    PRE_PROCESS=9
    POST_PROCESS=10

class ZoneTransition:
    def __init__(self, data):
        self.transition_id=data.get('transition_id', None) 
        self.curr_zone_id = data.get('curr_zone', None)  # Default to 0 if missing
        self.curr_phases = [ZonePhase(phase) for phase in data.get('curr_phases')]
        self.next_zone_id = data.get('next_zone', None)
        self.next_phases = [ZonePhase(phase) for phase in data.get('next_phases')]        
        self.colors = data.get('color',[]) if isinstance(data.get('color',[]),list) else [data.get('color')]
        self.types = data.get('type',[]) if isinstance(data.get('type',[]),list) else [data.get('type')]
        self.transit = data.get('transit', None)
        self.centrifuged = data.get('centrifuged', None)
        self.item_type = ItemType(data.get('item_type'))
        self.post_operations = data.get('post_operations', None)
        self.pre_operations = data.get('pre_operations', None)
        self.pre_checks = data.get('pre_checks', None)
        self.orig_trans_ids = data.get('orig_transitioins', None)
        self.possible_next_trans_ids = data.get('possible_next_transitions', None)
        self.no_curr_phase_change = data.get('no_curr_phase_change', 0)
        self.no_next_phase_change = data.get('no_next_phase_change', 0)
        self.curr_order_by =data.get('curr_order_by',None)        

class AppData:
    def __init__(self):
        app_data=config['app']
        self.app_id=app_data['app_id']
        self.host:str = app_data['host']
        self.port:int = app_data['port']
        self.audit_path:str = app_data['audit_path']
        self.audit_level:str = app_data['audit_level']
        self.rtde_ip: str = app_data['rtde_ip']
        self.festo_ip: str = app_data['festo_ip']
        self.camera1_ip: str = app_data['camera1_ip']
        self.camera2_ip: str = app_data['camera2_ip']
        self.transits_ip: str = app_data['transits_ip']
        self.transits_port: int = app_data['transits_port']
        self.decap_port: str = app_data['decap_port']
        self.centri_port: str = app_data['centri_port']
        self.zone_locks:Dict[int, List[asyncio.Lock]] = {}
        self.color_type_map = app_data.get('color_type_map',None) 
        self.cam1_jobs:int = app_data.get('cam1_jobs',0) 
        self.cam1_col:str=app_data.get('cam1_col','') 
        self.cam1_rows:list= app_data.get('cam1_rows',None) 
        self.cam2_color: str =app_data.get('cam2_color','') 
        self.cam2_bc_bc: str =app_data.get('cam2_bc_bc','') 
        self.cam2_bc_ac: str =app_data.get('cam2_bc_ac','')
        self.reset() 

        global COLORS
        global ROBOTS
        global TRANSITS
        global VIAL_TYPE

        for name, value in app_data['colors'].items():
            COLORS[name]=value

        for name, value in app_data['robots'].items():
            ROBOTS[name]=value
            tasks_q[name]=[]
        
        TRANSITS=app_data['transits']

        for name, value in app_data['vial_types'].items():
            VIAL_TYPE[name]=value
    
    def reset(self):    
        self.cam1_sensor:bool =True
        if self.zone_locks:
            self.zone_locks.clear()

app_data:AppData=AppData()

@dataclass
class ResponseData:
    curr_zone: int = 0
    next_zone: int = 0
    curr_subzone: int = 0
    next_subzone: int = 0
    curr_wp: dict = field(default_factory=lambda: {'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0})
    next_wp: dict = field(default_factory=lambda: {'x': 0, 'y': 0, 'z': 0, 'rx': 0, 'ry': 0, 'rz': 0})
    curr_task: int = 0
    next_task: int = 0
    item_type: int = 0
    vial_type: int = 0
    random_id: int = 0
    color: int = 0
    decapped:int=0
