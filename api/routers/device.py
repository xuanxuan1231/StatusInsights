from fastapi import APIRouter
from data.device import *

router = APIRouter(prefix="/device", tags=["devices"])

@router.post('/register/{device_id}')
def register_device(device_id: str):
    pass

@router.post('/unregister/{device_id}')
async def unregister_device(device_id: str):
    pass

@router.get('/get')
async def get_all_devices():
    pass