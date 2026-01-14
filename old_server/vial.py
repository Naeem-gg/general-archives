from dataclasses import dataclass, field
import json
from random import choice, random
from datetime import datetime
import webcolors
from configuration import COLORS, VIAL_TYPE, ZoneTransition

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

    def __post_init__(self):
        # Ensure line_code is always a string to preserve leading zeros
        if hasattr(self, 'line_code'):
            original_value = self.line_code
            self.line_code = str(self.line_code)
            if original_value != self.line_code:
                print(f"DEBUG - Vial __post_init__: line_code converted from {original_value} (type: {type(original_value)}) to {self.line_code} (type: {type(self.line_code)})")
            else:
                print(f"DEBUG - Vial __post_init__: line_code unchanged: {self.line_code} (type: {type(self.line_code)})")

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
    
    def set_decapped(self):
        self.decapped=True

    def set_transit(self, transit):
        arch = "ARCH"        
        if transit not in self.transits:
            if arch in self.transits:
                self.transits[self.transits.index(arch)] = transit
            else:
                self.transits.append(transit)            
    
    def progress_transit(self): 
        arch = "ARCH"
        if not self.transits:
            self.transits.append(arch)
        elif len(self.transits) == 1:
            self.transits[0] = choice([arch,arch,arch,self.transits[0]])
        else:
            self.transits.pop(0)

    def matches(self, transition:'ZoneTransition'):
        return ((self.next_zone_id is None or transition.next_zone_id is None or self.next_zone_id == transition.next_zone_id) and
            (transition.transit is None or not self.transits or transition.transit == self.transits[0]) and
            (self.color is None or not transition.colors or self.color in transition.colors) and
            (self.type is None or not transition.types or self.type in transition.types) and
             (self.centrifuged is None or transition.centrifuged is None or self.centrifuged == transition.centrifuged)) 
    
    def export_data(self,is_gui):
        if is_gui:
            # DEBUG: Check line_code before export
            print(f"DEBUG - Vial export_data: line_code = {self.line_code} (type: {type(self.line_code)})")
            return {"added_time":self.added_time,"line_code":self.line_code,"color":COLORS[self.color],"color_hex":self.name_to_hex(COLORS[self.color]),"type":VIAL_TYPE[self.type],"fluid_level":self.fluid_level,"transits":self.transits}
        return json.dumps(self.__dict__)
    
    def name_to_hex(self,color:str):
        if not color:
            return None
        # print("BEFORE")
        # print(color)
        if (color == "CLEAR" or color == "PILOT"):
            color="WHITE"
        elif color == "BIGRED":
            color="RED"
        # print("COLOR")
        # print(COLORS[color])
        return webcolors.name_to_hex(str.lower(color))