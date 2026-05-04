from fastapi import APIRouter, status, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import Optional
from data.device import *
from data.config import require_api_key


class Device(BaseModel):
    device_id: str
    name: str
    device_type: str
    description: Optional[str]


class EditDeviceRequest(BaseModel):
    device_id: str
    model_config = ConfigDict(extra='allow')


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


@router.post('/edit', status_code=status.HTTP_200_OK, dependencies=[Depends(require_api_key)])
def edit_device(request: EditDeviceRequest):
    try:
        updates = request.model_dump(exclude={'device_id'}, exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No editable fields provided.')
        return edit(request.device_id, updates)
    except RuntimeError as e:
        print('Failed to edit device: ', e)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print('Failed to edit device: ', e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to edit device.')
