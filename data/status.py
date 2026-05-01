import time
from typing import Optional

import pymongo

from data.device import get as get_device
from data.config import DEVICE_OFFLINE_THRESHOLD_SECONDS, MONGODB_ENABLED, MONGODB_URI

DEVICE_STATUSES: list[dict[str, object]] = []
PERSON_STATUS: tuple[str, Optional[str]] = ('无状态', '还没有设置状态诶（')
PERSON_STATUS_DOCUMENT_ID = "person_status"

_person_status_collection = None
_device_status_collection = None

if MONGODB_ENABLED:
    if not MONGODB_URI:
        print("MONGODB_ENABLED is set but MONGODB_URI is missing; person status persistence is disabled.")
    else:
        try:
            _mongo_client = pymongo.MongoClient(MONGODB_URI)
            _person_status_collection = _mongo_client["status-insights"]["status"]
            _device_status_collection = _mongo_client["status-insights"]["device_statuses"]
        except Exception as exc:
            print(f"Failed to initialize MongoDB for person status: {exc}")


def _sanitize_statuses() -> None:
    global DEVICE_STATUSES
    # Drop malformed entries to avoid KeyError during summary or lookups.
    DEVICE_STATUSES = [
        status for status in DEVICE_STATUSES
        if isinstance(status, dict) and 'id' in status
    ]


def set_device_status(device_id: str, status: str):
    global DEVICE_STATUSES
    get_device(device_id) # 检查设备是否已经注册
    now = time.time()
    if _device_status_collection is not None:
        try:
            _device_status_collection.replace_one(
                {"_id": device_id},
                {"status": status, "last_seen": now},
                upsert=True,
            )
            return
        except Exception as exc:
            print(f"Failed to persist device status, falling back to memory: {exc}")
    _sanitize_statuses()
    for device_status in DEVICE_STATUSES:
        if device_status['id'] == device_id:
            device_status['status'] = status
            device_status['last_seen'] = now
            return
    DEVICE_STATUSES.append({'id': device_id, 'status': status, 'last_seen': now})

def get_device_status(device_id: str) -> Optional[dict[str, object]]:
    global DEVICE_STATUSES
    if _device_status_collection is not None:
        try:
            document = _device_status_collection.find_one({"_id": device_id})
            if isinstance(document, dict):
                status = document.get("status")
                if not isinstance(status, str):
                    status = str(status) if status is not None else "无状态"
                last_seen_raw = document.get("last_seen")
                try:
                    last_seen = float(last_seen_raw)
                except (TypeError, ValueError):
                    last_seen = 0.0
                return {"id": device_id, "status": status, "last_seen": last_seen}
        except Exception as exc:
            print(f"Failed to read device status from MongoDB, falling back to memory: {exc}")
    _sanitize_statuses()
    for device_status in DEVICE_STATUSES:
        if device_status['id'] == device_id:
            return device_status
    raise RuntimeError(f"Device with id {device_id} not found.")

def set_person_status(status: str, description: Optional[str]):
    global PERSON_STATUS
    PERSON_STATUS = (status, description)
    if _person_status_collection is None:
        return
    try:
        _person_status_collection.replace_one(
            {"_id": PERSON_STATUS_DOCUMENT_ID},
            {"status": status, "description": description},
            upsert=True,
        )
    except Exception as exc:
        print(f"Failed to persist person status: {exc}")

def get_person_status() -> tuple[str, Optional[str]]:
    global PERSON_STATUS
    if _person_status_collection is not None:
        try:
            document = _person_status_collection.find_one({"_id": PERSON_STATUS_DOCUMENT_ID})
            if isinstance(document, dict):
                status = document.get("status")
                if isinstance(status, str):
                    description = document.get("description")
                    if description is not None and not isinstance(description, str):
                        description = str(description)
                    PERSON_STATUS = (status, description)
        except Exception as exc:
            print(f"Failed to read person status from MongoDB: {exc}")
    return PERSON_STATUS

def _is_online(device_status: dict[str, object], now: float) -> bool:
    last_seen = device_status.get('last_seen')
    if last_seen is None:
        return False
    return (now - float(last_seen)) <= DEVICE_OFFLINE_THRESHOLD_SECONDS


def get_all_device_statuses(online_only: bool = False) -> list[dict[str, object]]:
    global DEVICE_STATUSES
    if _device_status_collection is not None:
        statuses: list[dict[str, object]] = []
        try:
            now = time.time()
            for document in _device_status_collection.find():
                if not isinstance(document, dict):
                    continue
                device_id = document.get("_id")
                if not isinstance(device_id, str):
                    continue
                status = document.get("status")
                if not isinstance(status, str):
                    status = str(status) if status is not None else "无状态"
                last_seen_raw = document.get("last_seen")
                try:
                    last_seen = float(last_seen_raw)
                except (TypeError, ValueError):
                    last_seen = 0.0
                parsed_status = {"id": device_id, "status": status, "last_seen": last_seen}
                if not online_only or _is_online(parsed_status, now):
                    statuses.append(parsed_status)
            return statuses
        except Exception as exc:
            print(f"Failed to list device statuses from MongoDB, falling back to memory: {exc}")
    _sanitize_statuses()
    statuses = list(DEVICE_STATUSES)
    if not online_only:
        return statuses
    now = time.time()
    return [status for status in statuses if _is_online(status, now)]
