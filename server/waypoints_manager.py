from dataclasses import dataclass
from typing import List
from configuration import ItemType
from pallet import waypoints,calculate_waypoints
from zone_manager import zone_manager
from zone import Zone
from event_tracker import pallet_auditor

@dataclass
class WaypointsManager:
    global waypoints
    
    async def register_waypoints(self,points:list,zone_ids:list[int],subzone_id:int=0,type:ItemType=ItemType.VIAL.value,robot_id:int=1):        
        pallet=[] 
               
        if len(zone_ids) == 1:
            zone_id=zone_ids[0]
            zone:Zone=zone_manager.get_zone(zone_id)
            if not zone: 
                raise "Invalid zone Id"
            
            if zone.subzones and type == ItemType.VIAL.value: # tube locations
                num_subzones =len(zone.subzones)               
                if subzone_id:
                    subzone:Zone=zone.get_subzone_by_id(subzone_id)
                    if not subzone: 
                        raise ValueError("Invalid sub zone Id")
                    if zone_id == 8:
                        pallet=calculate_waypoints(points,zone.rows,zone.columns,subzone.rows,subzone.columns)
                    else:
                        pallet=calculate_waypoints(points,subzone.rows,subzone.columns,subzone.rows,subzone.columns)
                    waypoints[(robot_id,zone_id,subzone_id,type)]= pallet
                    await self.audit_locations((robot_id,zone_id,subzone_id,type))
                else:
                    subzone=zone.subzones[0]
                    pallet=calculate_waypoints(points,zone.rows,zone.columns,subzone.rows,subzone.columns)
                    await self.devide_subzone_locations(pallet,num_subzones,zone_id,type,robot_id)
            else:
                pallet=calculate_waypoints(points,zone.rows,zone.columns,zone.rows,zone.columns,zone.pallets)
                waypoints[(robot_id,zone_id,subzone_id,type)]= pallet
                await self.audit_locations((robot_id,zone_id,subzone_id,type))
        else:
            total_rows = 0

            for zone_id in zone_ids:
                zone = zone_manager.get_zone(zone_id)
                total_rows += zone.rows
            zone_id=zone_ids[0]
            zone:Zone=zone_manager.get_zone(zone_id)
            pallet=calculate_waypoints(points,total_rows,zone.columns,total_rows,zone.columns)
            for zone_id in zone_ids:
                zone = zone_manager.get_zone(zone_id)
                locations_per_zone = zone.rows * zone.columns
                locations =pallet[0:locations_per_zone]
                del pallet[0:locations_per_zone]
                waypoints[(robot_id,zone_id,0,type)]  = locations
                await self.audit_locations((robot_id,zone_id,0,type))

    async def devide_subzone_locations(self,pallet,num_subzones,zone_id,type,robot_id):
        if num_subzones >0:
            if len(pallet) % num_subzones != 0:
                raise ValueError("The number of locations must be divisible by the number of subzones.")
            locations_per_subzone = len(pallet) // num_subzones        
            subzone_locations=[pallet[i:i + locations_per_subzone] for i in range(0, len(pallet), locations_per_subzone)]
            for i, locations in enumerate(subzone_locations):
                waypoints[(robot_id,zone_id,i+1,type)]  = locations
                await self.audit_locations((robot_id,zone_id,i+1,type))
        else:
            waypoints[(robot_id,zone_id,0,type)]  = pallet
            await self.audit_locations((robot_id,zone_id,0,type))

    async def audit_locations(self,key):        
        if key in waypoints:
            pallet_auditor.info(f"Pallet locations Robot:{key[0]} Zone:{key[1]} - SubZone: {key[2]}")
            for index, content in enumerate(waypoints[key]):
                pallet_auditor.info(f"Position- {index+1}: {content}")

    def restart(self):
        waypoints ={}

waypoints_manager = WaypointsManager()


