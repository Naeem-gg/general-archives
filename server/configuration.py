import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List
import webcolors
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
    INIT=8

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
        self.transits = data.get('transit',[]) if isinstance(data.get('transit',[]),list) else [data.get('transit')]
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
        self.target_zone_id = data.get('target_zone', None)  # Default to 0 if missing  
        self.pre_tasks = data.get('pre_tasks', None)
        self.pick_index=data.get('pick_index', None)
        self.place_index=data.get('place_index', None)
        self.emergency=data.get('emergency', False)
        self.disposable =data.get('disposable', False)
        self.zone_type =data.get('zone_type',None)
        self.control_process_check =data.get('control_process_check', False)
        
class AppData:
    def __init__(self):
        app_data=config['app']
        self.app_id=app_data['app_id']
        self.host:str = app_data['host']
        self.port:int = app_data['port']
        self.audit_path:str = app_data['audit_path']
        self.audit_level:str = app_data['audit_level']
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
        self.color_type_level_map = app_data.get('color_type_level_map',None)
        self.image_src_path = app_data.get('image_src_path',None)
        self.image_dest_path = app_data.get('image_dest_path',None)
        self.image_dest_path_remote = app_data.get('image_dest_path_remote',None)
        self.error_file_path = app_data.get('error_file_path',None)
        self.error_file_path_remote = app_data.get('error_file_path_remote',None)
        self.error_codes = app_data.get('error_codes',None)
        self.color_transit_map = app_data.get('color_transit_map',None)  
        self.sensors={}
        self.sftp_host = app_data.get('sftp_host',None)
        self.sftp_port = app_data.get('sftp_port',None) 
        self.sftp_user = app_data.get('sftp_user',None) 
        self.sftp_password = app_data.get('sftp_password',None)    
        self.safety_activated=False   
        self.sftp_active =app_data.get('sftp_active',0)
        self.popup_acknowledged= True
        self.disposal_time :int = app_data.get('disposal_time',None)  
        self.camera1_images_path = app_data.get('camera1_images_path',None)
        self.retention_period = app_data.get('retention_period',30)
        self.color_zone_map = app_data.get('color_zone_map',None)  
        self.zone_controls_map = {entry["rackzone"]: entry for entry in app_data.get('zone_controls_map',None)}
        self.controls_time= datetime.strptime("05:00", "%H:%M").time()

 
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
        self.popup_acknowledged =True

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
    curr_idx:int=0
    next_idx:int=0

class ErrorCodes(Enum):
    COLOR_FAIL = 1
    LINE_CODE_FAIL = 2
    LEVEL_FAIL = 3
    LIS_FAIL = 4
    UNKNOWN_FAIL =5

def name_to_hex(color:str):
    if not color:
        return None
    if color == "CLEAR" or color == "PILOT":
        color="WHITE"
    elif color == "BIGRED":
        color="RED" 
    elif color == "CONTROL":
        color="WHITE"
    return webcolors.name_to_hex(str.lower(color))

def name_to_rgb(color:str):
    if not color:
        return None
    return webcolors.name_to_rgb(str.lower(color))


@dataclass
class TransitData:
    line_code: str = ''
    transit: str = ''
    to_centrifuge: bool = False
    to_decap: bool = False    
    archive_type: str = "U"
    priority: str ="R"
