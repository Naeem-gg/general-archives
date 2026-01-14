import asyncio
import json
from aiohttp import web
from aiohttp_xmlrpc import handler
from event_tracker import error_auditor
from vial_manager import vial_manager
from zone_manager import zone_manager
from configuration import app_data
from cors_middleware import cors_middleware
class GlobalHandler(handler.XMLRPCView):

    async def rpc_restart(self,archiv_reset):
        try:
            vial_manager.restart()        
            await zone_manager.restart(archiv_reset)
        except Exception as e:
            print(e)
    
    async def rpc_get_archiv_data(self):
        data=await zone_manager.get_archiv_data()
        
        
        def force_line_code_strings(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "line_code":
                        # Force line_code to be a string AND escape it to prevent number conversion
                        line_code_str = str(value)
                        # Add a prefix to ensure XML-RPC treats it as a string, not a number
                        obj[key] = f"STR_{line_code_str}"
                        print(f"Debug - Escaped line_code: {value} -> {obj[key]}")
                    elif isinstance(value, (dict, list)):
                        force_line_code_strings(value)
            elif isinstance(obj, list):
                for item in obj:
                    force_line_code_strings(item)
        
        # Apply the clean fix to the entire data structure
        force_line_code_strings(data)
        
        print(json.dumps(data,indent=4))
        return data
    
    async def rpc_delete_vial_by_barcode(self,data):
        await asyncio.sleep(2)
        print(data)
        for barcode in data['barcodes']:
             await zone_manager.delete_vial_by_barcode(barcode)
        return True 
             
               
app = web.Application(middlewares=[cors_middleware])
app.router.add_route("*", "/", GlobalHandler)
web.run_app(app, host=app_data.host, port=app_data.port)