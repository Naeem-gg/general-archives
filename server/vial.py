from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from random import choice, random
from configuration import COLORS, VIAL_TYPE, TransitData, ZoneTransition,app_data
from event_tracker import tasks_auditor
import webcolors
@dataclass
class Vial:
    line_code:str
    color:int
    type:int
    current_zone_id:int=0
    current_subzone_id:int=0
    next_zone_id:int=0
    fluid_level:bool = True
    transits:list=field(default_factory=list) 
    centrifuged:bool =False
    decapped:bool =False
    error_code=None
    to_centrifuge:bool =None
    to_decap: bool =None
    archive_type:str =None
    emergency: bool= False
    added_time: str =datetime.now().isoformat()
    blood_bags:list=field(default_factory=list) 

    def set_zone(self,current_zone_id):
        self.current_zone_id=current_zone_id

    def set_subzone(self,subzone_id):
        self.current_subzone_id =subzone_id

    def set_next_zone(self,zone_id):
        self.next_zone_id=zone_id

    def move_to_next_zone(self):
        if self.next_zone_id:
            self.current_zone_id = self.next_zone_id.pop(0)
        else:
            print("No more zones to move to.")

    def set_centrifuged(self):
        self.centrifuged=True
    
    def set_decapped(self,decapped=True):
        self.decapped=decapped

    def set_transit(self, transit,bags=None):        
        archs = ["ARCH", "DIMM-ARCH", "SYSM-ARCH", "ORTH-ARCH","COAG-ARCH"]
        if transit not in self.transits and transit:
            replaced = False
            for arch in archs:
                if arch in self.transits:
                    self.transits[self.transits.index(arch)] = transit
                    replaced = True
                    break
            if not replaced:
                self.transits.append(transit)
        self.transits=self.get_valid_transits(self.transits) 
        self.add_bags(bags)           
    
    def progress_transit(self): 
        arch = "ARCH"
        if not self.transits:
            self.transits.append(arch)
        elif len(self.transits) == 1:
            self.transits[0] = arch
        else:
            self.transits.pop(0)

    def matches(self, transition:'ZoneTransition'):
        disposal_time =app_data.disposal_time
        added_dt= datetime.fromisoformat(self.added_time)
        return ((self.next_zone_id is None or transition.next_zone_id is None or self.next_zone_id == transition.next_zone_id) and
            (not transition.transits or not self.transits or self.transits[0] in transition.transits) and
            (self.color is None or not transition.colors or self.color in transition.colors) and
            (self.type is None or not transition.types or self.type in transition.types) and
            (self.centrifuged is None or transition.centrifuged is None or self.centrifuged == transition.centrifuged) and
            (transition.disposable is False or datetime.now() - added_dt > timedelta(seconds=disposal_time))) 
    
    def export_data(self,is_gui):
        if is_gui:
            color_key = int(self.color) if self.color is not None else None
            type_key = int(self.type) if self.type is not None else None
            color_name = COLORS[color_key] if color_key is not None and color_key in COLORS else None
            type_name = VIAL_TYPE[type_key] if type_key is not None and type_key in VIAL_TYPE else None
            return {"line_code":"STR_"+self.line_code,"color":color_name,"color_hex":self.name_to_hex(color_name),"type":type_name,"fluid_level":self.fluid_level,"transits":self.transits,"added_time":self.added_time}
        return json.dumps(self.__dict__)
   
    def get_transits_order(self):
        if not app_data.color_transit_map:
            return None
        for mapping in app_data.color_transit_map:
            if self.color in mapping['colors']:
                return mapping['transits']
        return None
    
    def get_valid_transits(self,transits):
        tasks_auditor.info(f"Transits before validation for {self.line_code}: {transits} ")     
        transits_order=self.get_transits_order()
        if not transits_order:
            return transits
        priority_index = {value: index for index, value in enumerate(transits_order)}
        transits = sorted(
            (transit for transit in transits if transit in priority_index),
            key=lambda x: priority_index[x])
        tasks_auditor.info(f"Transits after validation for {self.line_code}: {transits} ")
        return transits
    
    def set_transit_data(self, transit_data:TransitData):
        self.set_transit(transit_data.transit)
        if transit_data.to_centrifuge != '':
            self.to_centrifuge =transit_data.to_centrifuge == "Y"
        if transit_data.to_decap != '':
            self.to_decap =transit_data.to_decap == "Y"
        if transit_data.archive_type != '':
            self.archive_type =transit_data.archive_type
        if transit_data.priority != '':
            self.emergency= transit_data.priority == "A"
        
    def is_emergency(self):
        return self.emergency

    def add_bags(self,bags):
        if bags: 
            self.blood_bags=[]
            for bag in bags:
                if bag not in self.blood_bags:
                    self.blood_bags.append(bag)
            tasks_auditor.info(f"Pilots added for the sample: {self.line_code}: {self.blood_bags} ")
    def name_to_hex(self,color:str):
        if not color:
            return None
        # print("BEFORE")
        # print(color)
        if (color == "CLEAR" or color == "PILOT" or color == "COUNTER"):
            color="WHITE"
        elif color == "BIGRED":
            color="RED"
        # print("COLOR")
        # print(COLORS[color])
        return webcolors.name_to_hex(str.lower(color))