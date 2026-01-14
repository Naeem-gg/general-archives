import asyncio
from datetime import datetime
import os
from typing import Counter
from configuration import COLORS, TransitData,app_data,name_to_hex
from vial import Vial
from event_tracker import tasks_auditor,error_auditor

class VialManager:

    def __init__(self, vials:list[Vial]=[]):
        self.vials:list[Vial]=vials
    
    def add_vial(self,vial:Vial):
        self.vials.append(vial)

    def get_vial(self, line_code=None):
        if line_code :
            return next((vial for vial in self.vials if vial.line_code == line_code), None)
        return None
    
    def set_transit(self, line_code:str,transit:str,bags=None):
        for vial in self.vials:
            if vial.line_code == line_code:
                vial.set_transit(transit,bags)
                return True
        return False 
    
    def restart(self):
        self.vials=[]
    
    def validate_line_code(self,line_code):
        vial=self.get_vial(line_code) 
        if vial and vial.current_zone_id in (10,101,102):
            vial.line_code= vial.line_code+'000'
    
    def delete_vial(self,vial:Vial):
        if vial: 
            self.vials.remove(vial)    

    def set_transit_data(self, transit_data:TransitData):
        for vial in self.vials:
            if vial.line_code == transit_data.line_code:
                vial.set_transit_data(transit_data)
                return True
        return False

    def is_duplicate_vial(self,line_code):
        if line_code:
            return sum(1 for vial in self.vials if vial.line_code == line_code and vial.current_zone_id != 10) >= 1

vial_manager: VialManager= VialManager()
