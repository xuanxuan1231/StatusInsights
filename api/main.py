from fastapi import FastAPI

from api.routers.device import router as device_router
from api.routers.status import router as status_router

app = FastAPI()

app.include_router(device_router)
app.include_router(status_router)