import asyncio
from datetime import datetime
from aiohttp_xmlrpc import handler
from futures_manager import futures_manager
from utils import acquire_zone_lock, release_zone_lock
from waypoints_manager import waypoints_manager
from zone_manager import zone_manager
from configuration import app_data, VIAL_TYPE, COLORS, TRANSITS, ZonePhase
from vial_manager import vial_manager
from event_tracker import tasks_auditor
from random import choice

class GlobalHandler(handler.XMLRPCView):
    async def rpc_restart(self,archiv_reset=True):
        try:
            vial_manager.restart()        
            await zone_manager.restart(archiv_reset)
            waypoints_manager.restart()
            app_data.reset()
            zone_manager.file_loaded=True
            await self.rpc_prepare_test_data(results=[])
            tasks_auditor.info("Robot Restarted Successfully") 
            #asyncio.create_task(monitor_get_task_util())
        except Exception as e:
            print(e)
    
    async def refresh_data(self,archiv_reset=False):
        vial_manager.restart()        
        await zone_manager.restart(archiv_reset)
        waypoints_manager.restart()
        app_data.reset()

    async def rpc_task(self): 
        return 1

    async def rpc_get_task(self,random_id,robot_id):
        await futures_manager.execute_future(random_id)
        task= await zone_manager.get_task(robot_id)
        
        # Print task response in human-readable format
        print("\n" + "="*60)
        print(f"📋 GET_TASK Response (random_id={random_id}, robot_id={robot_id})")
        print("="*60)
        print(f"  Current Zone:     {task.get('curr_zone', 'N/A')}")
        print(f"  Next Zone:        {task.get('next_zone', 'N/A')}")
        print(f"  Current Subzone:  {task.get('curr_subzone', 'N/A')}")
        print(f"  Next Subzone:     {task.get('next_subzone', 'N/A')}")
        print(f"  Current Index:    {task.get('curr_idx', 'N/A')}")
        print(f"  Next Index:       {task.get('next_idx', 'N/A')}")
        print("="*60 + "\n")
        
        return task
    
    async def rpc_update_camera2_result(self,is_success,type,random_id):
        await futures_manager.execute_future(random_id)
        await zone_manager.update_camera2_result_test_1006(bool(is_success),None)
        return
        
    async def rpc_update_camera14_result(self,is_present,random_id):
        await futures_manager.execute_future(random_id)
        return await zone_manager.update_camera14_result(is_present)

    async def rpc_init_vial(self,is_present,random_id):
        await futures_manager.execute_future(random_id)
        return await zone_manager.init_vial(is_present)

    async def rpc_acquire_zone_lock(self,lock_id: int, robot_id: int):
        await acquire_zone_lock(lock_id, robot_id)
    
    async def rpc_release_zone_lock(self,lock_id: int, robot_id: int):
        await release_zone_lock(lock_id, robot_id)

    async def rpc_register_waypoints(self,points,zone_id,subzone_id,type,robot_id): 
        return await waypoints_manager.register_waypoints(points,zone_id,subzone_id,type,robot_id)
    
    async def rpc_execute_future(self,random_id):
        await futures_manager.execute_future(random_id)
    
    async def rpc_set_centri_runtime(self):
        await zone_manager.set_centri_run_time()

    async def rpc_update_camera2_result_test(self,is_success,type,random_id,appId):
        await futures_manager.execute_future(random_id)
        if appId == 1001:
            await zone_manager.update_camera2_result_test_1001(is_success,type)
        elif appId == 1002:
            await zone_manager.update_camera2_result_test_1002(is_success,type)
        elif appId == 1004:
            await zone_manager.update_camera2_result_test_1004(is_success,type)
        elif appId == 1005:
            await zone_manager.update_camera2_result_test_1005(is_success,type)
        elif appId == 1006:
            await zone_manager.update_camera2_result_test_1006(is_success,type)
        return
    
    async def rpc_get_archiv_data(self):
        if not zone_manager.file_loaded:
            await self.refresh_data(False)
            tasks_auditor.info("Data got refreshed as file is not loaded.")
            zone_manager.file_loaded=True
        data=await zone_manager.get_archiv_data()
        return data
    
    async def rpc_get_data(self):
        data=await zone_manager.get_data()
        return data
    
    async def rpc_delete_vial_by_barcode(self,data):
        for barcode in data['barcodes']:
             await zone_manager.delete_vial_by_barcode(str(barcode))
        await zone_manager.reset_empty_archives()
        return True
    
    async def rpc_reset_archives(self,zone_id=None):
        await zone_manager.reset_archives(zone_id)        
        app_data.popup_acknowledged =True 
        return True
    
    async def rpc_progress_transit_test(self):
        zone_manager.progress_transit_test()
        return True
    
    async def rpc_reset_fehler(self):
        await zone_manager.reset_fehler()
        app_data.popup_acknowledged =True 
        return True
    
    async def rpc_popup_acknowledged(self):        
        return app_data.popup_acknowledged
    
    async def rpc_set_popup_acknowledged(self):        
        app_data.popup_acknowledged =True

    async def rpc_camera1_exists(self):
        return await zone_manager.camera1_exists()

    async def rpc_prepare_test_data(self,results):
        results = self.get_results()
        await zone_manager.prepare_data(results)
        return True

    async def rpc_add_controls(self):        
        return await zone_manager.add_controls()
    
    async def rpc_set_controls_time(self,time_val):    
        app_data.controls_time = datetime.strptime(time_val, "%H:%M").time() 
        return True      

    async def rpc_change_device_state(self,id,val):  
        return await zone_manager.change_device_active(id,val)
    
    async def rpc_set_disposal_time(self,time_val):    
        app_data.disposal_time = datetime.strptime(time_val, "%H:%M").time() 
        return True
    
    async def rpc_extend_runtime(self,zone_id,subzone_id):
        await zone_manager.extend_runtime(zone_id,subzone_id)
    
    async def rpc_bin_cleared(self):
        await zone_manager.clear_dustbin()
    async def rpc_edit_data(self,results):
        print("Editing Data")
        print(results)
    async def rpc_add_new_tube(self,data):
        print("Adding New Tube")
        print(data)    
    
    async def rpc_get_tube_types(self):

        return VIAL_TYPE
    
    async def rpc_get_colors(self):
        return COLORS
    async def rpc_get_transits(self):
        return TRANSITS
    
    async def rpc_get_phases(self):
        kv = {e.name: e.value for e in ZonePhase}
        return kv
    
    async def rpc_edit_phases(self, data):
        print("Editing Phases")
        print(data)
        # data structure:
        # - For zone phase: {'zone_id': <id>, 'phase': <phase_value>}
        # - For subzone phase: {'zone_id': <parent_zone_id>, 'subzone_id': <subzone_id>, 'phase': <phase_value>}
        zone_id = data.get('zone_id')
        subzone_id = data.get('subzone_id')
        phase = data.get('phase')
        
        if subzone_id:
            print(f"Updating subzone {subzone_id} in zone {zone_id} to phase {phase}")
        else:
            print(f"Updating zone {zone_id} to phase {phase}")

    def get_results(self):
        results =[]
        for i in range(35):
            results.append((i+1,choice([1,2,3,4,8]))) #,1,2,3,4,8
        
        for i in range(60,65):
            results.append((i+1,choice([9])))
        
        for i in range(70,80):
            results.append((i+1,choice([10])))
        return results