from fastapi import APIRouter, status, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from data.device import *
from data.config import require_api_key

class Device(BaseModel):
    device_id: str
    name: str
    device_type: str
    description: Optional[str]

router = APIRouter(prefix="/device", tags=["devices"])

@router.post('/register', status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
def register_device(device: Device):
    try:
        register(device.name, device.device_id, device.device_type, device.description)
        print(f'Registered device {device.name}({device.device_type}, {device.device_id}).')
    except Exception as e:
        print('Failed to register device: ', e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to register device.')

@router.delete('/unregister/{device_id}', status_code=status.HTTP_200_OK, dependencies=[Depends(require_api_key)])
def unregister_device(device_id: str):
    try:
        unregister(device_id)
    except Exception as e:
        print('Failed to unregister device: ', e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to unregister device.')

@router.get('/get')
def get_all_devices():
    try:
        return get_all()
    except Exception as e:
        print('Failed to get devices: ', e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to get devices.')