from typing import Counter
from configuration import COLORS
from vial import Vial
from event_tracker import tasks_auditor

class VialManager:

    def __init__(self, vials:list[Vial]=[]):
        self.vials:list[Vial]=vials
    
    def add_vial(self,vial:Vial):
        self.vials.append(vial)

    def get_vial(self, line_code=None):
        if line_code :
            return next((vial for vial in self.vials if vial.line_code == line_code), None)
        return None
    
    def set_transit(self, line_code:str,transit:str):
        for vial in self.vials:
            if vial.line_code == line_code:
                vial.set_transit(transit)
                return True
        return False
    
    def displayCounts(self):
        # Extract the colors from the list of items
        colors = [vial.color for vial in self.vials]

        # Use Counter to count occurrences of each color
        color_count = Counter(colors)

        # Print the number of items for each color
        for color, count in color_count.items():
            print(f"{COLORS[color]}: {count}")
    
    def restart(self):
        self.vials=[]
    
    def validate_line_code(self,line_code):
        vial=self.get_vial(line_code) 
        if vial and vial.current_zone_id ==10:
            vial.line_code= vial.line_code+'000'

    def delete_vial(self,vial:Vial):
        if vial: 
            self.vials.remove(vial)
            

vial_manager: VialManager= VialManager()
