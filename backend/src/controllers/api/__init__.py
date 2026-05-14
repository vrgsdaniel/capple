from src.controllers.api.battery_logs import router as battery_logs_router
from src.controllers.api.infrastructure import router as infrastructure_router
from src.controllers.api.users import router as users_router
from src.controllers.api.chat import router as chat_router

routers = [infrastructure_router, users_router, battery_logs_router, chat_router]
