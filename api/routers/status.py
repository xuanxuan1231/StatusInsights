from fastapi import APIRouter, Depends, HTTPException, status
import data.status as status_data
from data.config import require_api_key, NAME
from data.device import get_all as get_all_devices
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class DeviceStatusRequest(BaseModel):
    device_id: str
    status: str
    battery: Optional[int] = None
    signal_level: Optional[int] = None
    network_type: Optional[Literal['wifi', 'cellular', 'ethernet', 'none', 'unknown']] = None
    model_config = ConfigDict(extra='allow')


class PersonStatus(BaseModel):
    status: str
    description: Optional[str]


class DeviceSummary(BaseModel):
    device_id: str
    name: str
    device_type: str
    description: Optional[str]
    status: Optional[str]
    battery: Optional[int] = None
    signal_level: Optional[int] = None
    network_type: Optional[Literal['wifi', 'cellular', 'ethernet', 'none', 'unknown']] = None
    last_report_time: Optional[float] = None
    is_online: bool = False


class SummaryResponse(BaseModel):
    name: str
    person: PersonStatus
    devices: list[DeviceSummary]


router = APIRouter(prefix='/status', tags=['status'])


@router.post('/person/set', dependencies=[Depends(require_api_key)], status_code=201)
def set_person_status(status: PersonStatus):
    """
    设置人的状态。
    :return:
    """
    status_data.set_person_status(status.status, status.description)


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
        status_data.set_device_status(
            request.device_id,
            request.status,
            battery=request.battery,
            signal_level=request.signal_level,
            network_type=request.network_type,
        )
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
    all_statuses = status_data.get_all_device_statuses(online_only=False)
    online_statuses = status_data.get_all_device_statuses(online_only=True)
    online_ids = {item['id'] for item in online_statuses if 'id' in item}
    device_status_map = {item['id']: item for item in all_statuses if 'id' in item}
    device_summaries: list[DeviceSummary] = []
    for device in get_all_devices():
        if not isinstance(device, dict) or 'id' not in device:
            continue
        device_status = device_status_map.get(device['id'], {})
        device_summaries.append(
            DeviceSummary(
                device_id=device['id'],
                name=device['name'],
                device_type=device['type'],
                description=device.get('description'),
                status=device_status.get('status') if isinstance(device_status, dict) else None,
                battery=device_status.get('battery') if isinstance(device_status, dict) else None,
                signal_level=device_status.get('signal_level') if isinstance(device_status, dict) else None,
                network_type=device_status.get('network_type') if isinstance(device_status, dict) else None,
                last_report_time=device_status.get('last_report_time') if isinstance(device_status, dict) else None,
                is_online=device['id'] in online_ids,
            )
        )
    return SummaryResponse(
        name=NAME,
        person=PersonStatus(status=person_status, description=person_description),
        devices=device_summaries,
    )
