import time
from typing import Optional

from data.device import get as get_device
from data.config import DEVICE_OFFLINE_THRESHOLD_SECONDS

DEVICE_STATUSES: list[dict[str, object]] = []
PERSON_STATUS: tuple[str, Optional[str]] = ('无状态', '还没有设置状态诶（')


def _sanitize_statuses() -> None:
    global DEVICE_STATUSES
    # Drop malformed entries to avoid KeyError during summary or lookups.
    DEVICE_STATUSES = [
        status for status in DEVICE_STATUSES
        if isinstance(status, dict) and 'id' in status
    ]


def set_device_status(device_id: str, status: str):
    global DEVICE_STATUSES
    _sanitize_statuses()
    get_device(device_id) # 检查设备是否已经注册
    now = time.time()
    for device_status in DEVICE_STATUSES:
        if device_status['id'] == device_id:
            device_status['status'] = status
            device_status['last_seen'] = now
            return
    DEVICE_STATUSES.append({'id': device_id, 'status': status, 'last_seen': now})

def get_device_status(device_id: str) -> Optional[dict[str, object]]:
    global DEVICE_STATUSES
    _sanitize_statuses()
    for device_status in DEVICE_STATUSES:
        if device_status['id'] == device_id:
            return device_status
    raise RuntimeError(f"Device with id {device_id} not found.")

def set_person_status(status: str, description: Optional[str]):
    global PERSON_STATUS
    PERSON_STATUS = (status, description)

def get_person_status() -> tuple[str, Optional[str]]:
    global PERSON_STATUS
    return PERSON_STATUS

def _is_online(device_status: dict[str, object], now: float) -> bool:
    last_seen = device_status.get('last_seen')
    if last_seen is None:
        return False
    return (now - float(last_seen)) <= DEVICE_OFFLINE_THRESHOLD_SECONDS


def get_all_device_statuses(online_only: bool = False) -> list[dict[str, object]]:
    global DEVICE_STATUSES
    _sanitize_statuses()
    statuses = list(DEVICE_STATUSES)
    if not online_only:
        return statuses
    now = time.time()
    return [status for status in statuses if _is_online(status, now)]
