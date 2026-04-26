from fastapi import APIRouter, Depends, HTTPException, status
import data.status as status_data
from data.config import require_api_key, NAME
from data.device import get_all as get_all_devices
from typing import Optional
from pydantic import BaseModel

class DeviceStatusRequest(BaseModel):
    device_id: str
    status: str

class PersonStatus(BaseModel):
    status: str
    description: Optional[str]

class DeviceSummary(BaseModel):
    device_id: str
    name: str
    device_type: str
    description: Optional[str]
    status: Optional[str]

class SummaryResponse(BaseModel):
    name: str
    person: PersonStatus
    devices: list[DeviceSummary]

router = APIRouter(prefix='/status', tags=['status'])


@router.post('/person/set', dependencies=[Depends(require_api_key)],status_code=201)
def set_person_status(status: str, description: Optional[str]):
    """
    设置人的状态。
    :return:
    """
    status_data.set_person_status(status, description)


@router.get('/person/get')
def get_person_status() -> tuple[str, Optional[str]]:
    """
    获取人的当前状态。
    :return:
    """
    return status_data.get_person_status()


@router.post('/person/unset', dependencies=[Depends(require_api_key)], status_code=201)
def unset_person_status():
    """
    设置人的当前状态为空。
    :return:
    """
    status_data.set_person_status("无状态", None)


@router.post('/device/set', dependencies=[Depends(require_api_key)], status_code=201)
def set_device_status(request: DeviceStatusRequest):
    try:
        status_data.set_device_status(request.device_id, request.status)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get('/device/get/{device_id}')
def get_device_status(device_id: str):
    try:
        return status_data.get_device_status(device_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get('/summary', response_model=SummaryResponse)
def get_summary():
    person_status, person_description = status_data.get_person_status()
    online_statuses = status_data.get_all_device_statuses(online_only=True)
    status_map = {item['id']: item.get('status') for item in online_statuses if 'id' in item}
    online_ids = set(status_map.keys())
    device_summaries: list[DeviceSummary] = []
    for device in get_all_devices():
        if not isinstance(device, dict) or 'id' not in device:
            continue
        if device['id'] not in online_ids:
            continue
        device_summaries.append(
            DeviceSummary(
                device_id=device['id'],
                name=device['name'],
                device_type=device['type'],
                description=device.get('description'),
                status=status_map.get(device['id']),
            )
        )
    return SummaryResponse(
        name=NAME,
        person=PersonStatus(status=person_status, description=person_description),
        devices=device_summaries,
    )
