
from aiohttp import web
from rpc_handler import GlobalHandler
from utils import acquire_zone_lock, release_zone_lock
from configuration import app_data
from event_tracker import tasks_auditor,error_auditor

# REST API Handlers
async def restart(request):
    archiv_reset = request.query.get('archiv_reset', False)
    return web.Response(text=await GlobalHandler.rpc_restart(GlobalHandler,archiv_reset))

async def get_task(request):
    if request.headers.get("content-type") == "application/json":
        content=await request.json()
    else:
        content=request.query
    random_id = content.get('random_id')
    robot_id = content.get('robot_id')
    task = await GlobalHandler.rpc_get_task(GlobalHandler,int(random_id),int(robot_id))
    return web.json_response(task)

async def update_camera2_result(request):
    is_success = request.query.get('is_success')
    type = request.query.get('type')
    random_id = request.query.get('random_id')
    task = await GlobalHandler.rpc_update_camera2_result(GlobalHandler,bool(is_success),type,random_id)
    return web.Response(text= task)

async def set_camera_flag(request):
    """
        This method is called when there is ping from the user
    """
    try:
        tasks_auditor.info(f"Set camera flag command recieved")   
        app_data.cam1_sensor=True
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def set_sensor_flag(request):
    """
        This method is called when any of machine sensor value is changed
    """
    try:
        command = await request.json()
        tasks_auditor.info(f"Set sensor command recieved: {command}")   
        app_data.sensors[int(command['id'])]= command['val'] 
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 

async def reset_archives(request):
    """
        This method is called when there is ping from the user
    """
    try:
        command = await request.json()
        zone_id=None
        if 'zone_id' in command:
            zone_id=command['zone_id']
        tasks_auditor.info(f"reset archives command recieved")   
        await GlobalHandler.rpc_reset_archives(GlobalHandler,zone_id)
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def reset_fehler(request):
    """
        This method is called when there is ping from the user
    """
    try:
        tasks_auditor.info(f"reset fehler command recieved")   
        await GlobalHandler.rpc_reset_fehler(GlobalHandler)
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def register_waypoints(request):
    data = await request.json()
    result = await GlobalHandler.rpc_register_waypoints(GlobalHandler,
        data['points'], data['zone_id'], data['subzone_id'], data['type'], data['robot_id']
    )
    return web.json_response(result)

async def acquire_lock(request):
    content=await request.json()
    lock_id = content.get('lock_id')
    robot_id = content.get('robot_id')
    await acquire_zone_lock(lock_id, robot_id)
    return web.json_response({"result": True})

async def release_lock(request):
    content=await request.json()
    lock_id = content.get('lock_id')
    robot_id = content.get('robot_id')
    await release_zone_lock(lock_id, robot_id)
    return web.json_response({"result": True})

async def test(request):
    return web.json_response({"result": True})

async def set_camera1_results(request,error_flag: bool=False,error_code:str=""):
    """
        This method is called when there is ping from the user
    """
    try:
        if not error_flag:
            content=await request.json()
            tasks_auditor.info(f"Set camera flag command recieved") 
            await GlobalHandler.rpc_set_camera1_results(GlobalHandler,content) 
        else:
            error_auditor.info(f"Error occured in the camera interface: {error_code}")
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)


async def park_robot(request={}):    
    try:
        tasks_auditor.info(f"park robot command recieved")  
        await GlobalHandler.rpc_init_festo(GlobalHandler)      
        await GlobalHandler.rpc_festo_move(GlobalHandler,5100,1200,0)
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 

async def shutdown_handler(request={}):    
    try:
        tasks_auditor.info(f"shutdown recieved")  
        await GlobalHandler.rpc_shutdown(GlobalHandler)     
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 


async def add_controls(request={}):    
    try:
        tasks_auditor.info(f"add controls command recieved")  
        await GlobalHandler.rpc_add_controls(GlobalHandler)
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 

async def set_controls_time(request={}):    
    try:
        command = await request.json()
        tasks_auditor.info(f"set controls time command recieved: {command}")
        await GlobalHandler.rpc_set_controls_time(GlobalHandler,command['val'])
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 

async def change_device_state(request={}):    
    try:
        command = await request.json()
        tasks_auditor.info(f"change device state command recieved: {command}")
        result=await GlobalHandler.rpc_change_device_state(GlobalHandler,command['id'],command['val'])
        return web.json_response({"result": result})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 

async def set_disposal_time(request={}):    
    try:
        command = await request.json()
        tasks_auditor.info(f"set disposal time command recieved: {command}")
        await GlobalHandler.rpc_set_disposal_time(GlobalHandler,command['val'])
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def inform_robot_stop(request={}):    
    try:
        command = await request.json()
        tasks_auditor.info(f"inform_robot_stop command recieved: {command}")
        await GlobalHandler.rpc_inform_robot_stop(GlobalHandler)
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 

async def set_popup_acknowledged(request={}):    
    try:
        tasks_auditor.info(f"popup acknowledged command recieved")
        await GlobalHandler.rpc_set_popup_acknowledged(GlobalHandler)
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 

async def bin_cleared(request={}):    
    try:
        command = await request.json()
        tasks_auditor.info(f"bin_cleared command recieved: {command}")
        await GlobalHandler.rpc_bin_cleared(GlobalHandler,)
        return web.json_response({"result": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400) 
    
async def init_vial(request={}):    
    is_present = request.query.get('is_present')
    random_id = request.query.get('random_id')
    task = await GlobalHandler.rpc_init_vial(GlobalHandler,bool(is_present),str(random_id))
    return web.Response(text= task)
    
def add_rest_routes(app:web.Application):
    app.router.add_post('/restart', restart)
    app.router.add_get('/get_task', get_task)
    app.router.add_post('/set_camera_flag', set_camera_flag)
    app.router.add_post('/set_sensor_flag', set_sensor_flag)
    app.router.add_post('/reset_archives', reset_archives)
    app.router.add_post('/reset_fehler', reset_fehler)
    app.router.add_post('/update_camera2_result', update_camera2_result)
    app.router.add_post('/acquire_lock', acquire_lock)
    app.router.add_post('/release_lock', release_lock)
    app.router.add_post('/register_waypoints', register_waypoints)
    app.router.add_post('/set_camera1_results', set_camera1_results)
    app.router.add_post('/park_robot', park_robot)
    app.router.add_post('/shutdown', shutdown_handler)
    app.router.add_post('/add_controls', add_controls)
    app.router.add_post('/set_controls_time', set_controls_time)
    app.router.add_post('/change_device_state', change_device_state)
    app.router.add_post('/inform_robot_stop', inform_robot_stop)
    app.router.add_post('/popup_acknowledged', set_popup_acknowledged)
    app.router.add_post('/bin_cleared', bin_cleared)
    app.router.add_post('/test', test)
    app.router.add_post('/init_vial',init_vial)