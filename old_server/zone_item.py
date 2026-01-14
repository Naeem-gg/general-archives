from dataclasses import dataclass
from enum import Enum
from configuration import ZoneTransition
from vial import Vial

class ZoneItem:
    def __init__(self, item,content:Vial): 
        self.content:Vial=content
        if isinstance(item, list):
            self.position=item[0]
            self.types =item[1] if isinstance(item[1],list) else [item[1]]
        else:
            self.position=item
            self.types= None
            
        self.color =None        
        self.transit=None
    
    def set_content(self, content:Vial):
        self.content=content
    
    def remove_content(self):
        self.content=None
    
    def matches(self, transition:ZoneTransition):
        return ((self.transit is None or transition.transit is None or self.transit == transition.transit) and
            (self.color is None or not transition.colors or self.color in transition.colors) and
            (not self.types or not transition.types or any(type in transition.types for type in self.types))) 
    
    def export_data(self,is_gui):
        return {"position":self.position ,"content": self.content.export_data(is_gui)}