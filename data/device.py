import pymongo
import time
from typing import Optional

from data.config import MONGODB_ENABLED, MONGODB_URI, DEVICE_CACHE_TTL_SECONDS

DEVICES = []
CACHE_TTL_SECONDS = int(DEVICE_CACHE_TTL_SECONDS)
_LAST_REFRESH = 0.0

if MONGODB_ENABLED:
    mongo_uri = MONGODB_URI
    if not mongo_uri:
        print("MONGODB_ENABLED is set but MONGODB_URI is missing; disabling MongoDB.")
        MONGODB_ENABLED = False
    else:
        client = pymongo.MongoClient(mongo_uri)
        db = client["status-insights"]
        collection = db["devices"]


def _normalize_device(device: dict) -> Optional[dict]:
    if not isinstance(device, dict):
        return None
    if 'id' not in device:
        return None
    if 'name' not in device or 'type' not in device:
        return None
    normalized = {
        'id': device['id'],
        'name': device['name'],
        'type': device['type'],
        'description': device.get('description'),
    }
    for key, value in device.items():
        if key in normalized or key == '_id':
            continue
        normalized[key] = value
    return normalized


def update(force: bool = False) -> None:
    global DEVICES, _LAST_REFRESH
    if not MONGODB_ENABLED:
        return
    now = time.time()
    if not force and _LAST_REFRESH and (now - _LAST_REFRESH) < CACHE_TTL_SECONDS:
        return
    device_list = []
    try:
        for device in collection.find():
            normalized = _normalize_device(device)
            if normalized is not None:
                device_list.append(normalized)
        DEVICES = device_list
        _LAST_REFRESH = now
    except Exception as e:
        print(f"Failed to update devices: {e}")


def register(name: str, device_id: str, device_type: str, description: Optional[str]) -> None:
    """
    向数据库中写入一个设备的信息。
    :param name: 设备名称
    :param device_id: 设备的 GUID，必须唯一
    :param device_type: 设备类型
    :param description: 设备介绍，可选
    :return:
    """
    global DEVICES
    if MONGODB_ENABLED:
        update()
    if device_type not in ['win', 'mac', 'linux', 'ios', 'android', 'unknown']:
        raise ValueError(f"Invalid device type: {device_type}")
    for device in DEVICES:
        if device['id'] == device_id:
            raise ValueError(f"Device with id {device_id} already exists.")
    device_document = {
        'id': device_id,
        'name': name,
        'description': description,
        'type': device_type
    }
    if MONGODB_ENABLED:
        result = collection.insert_one(device_document)
        print(result)
        update(force=True)
    else:
        DEVICES.append(device_document)


def unregister(device_id: str):
    """
    从数据库中删除一个设备的信息。
    :param device_id: 设备 GUID。
    :return:
    """
    global DEVICES
    if MONGODB_ENABLED:
        update()
        for device in DEVICES:
            if device['id'] == device_id:
                result = collection.delete_many({'id': device_id})
                print(result)
                update(force=True)
                return
        raise RuntimeError(f"Device with id {device_id} not found.")
    else:
        for index, device in enumerate(DEVICES):
            if device['id'] == device_id:
                DEVICES.pop(index)
                print(f"Popped {index}: {device}.")
                return
        raise RuntimeError(f"Device with id {device_id} not found.")


def edit(device_id: str, updates: dict[str, object]) -> dict:
    """
    编辑设备信息。禁止编辑 id 与 type 字段。
    :param device_id: 设备 GUID。
    :param updates: 要更新的字段字典。
    :return: 更新后的设备信息。
    """
    global DEVICES
    if not isinstance(updates, dict) or not updates:
        raise ValueError("No editable fields provided.")
    if 'id' in updates or 'type' in updates:
        raise ValueError("Device id and type are not editable.")

    if MONGODB_ENABLED:
        update()
        result = collection.update_one({'id': device_id}, {'$set': updates})
        if result.matched_count == 0:
            raise RuntimeError(f"Device with id {device_id} not found.")
        update(force=True)
        return get(device_id)

    for device in DEVICES:
        if device['id'] == device_id:
            device.update(updates)
            return device
    raise RuntimeError(f"Device with id {device_id} not found.")


def get(device_id: str) -> Optional[dict]:
    """
    从数据库中获取一个设备的信息。
    :param device_id: 设备 GUID。
    :return:
    """
    global DEVICES
    if MONGODB_ENABLED:
        update()
    for device in DEVICES:
        if device['id'] == device_id:
            return device
    raise RuntimeError(f"Device with id {device_id} not found.")


def get_all() -> list[dict]:
    global DEVICES
    if MONGODB_ENABLED:
        update()
    return [device for device in DEVICES if _normalize_device(device) is not None]
