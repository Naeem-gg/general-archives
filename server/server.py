from aiohttp import web
from cors_middleware import cors_middleware
from event_tracker import tasks_auditor
from rpc_handler import GlobalHandler
from configuration import app_data
from rest_handler import add_rest_routes

async def shutdown(app):
    tasks_auditor.info("Server terminated Successfully") 

app = web.Application(middlewares=[cors_middleware])
app.router.add_route("*", "/", GlobalHandler)
add_rest_routes(app)
app.on_cleanup.append(shutdown)

web.run_app(app, host=app_data.host, port=app_data.port)

  
