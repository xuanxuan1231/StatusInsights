import pymongo
import os
from typing import Optional

MONGODB_ENABLED = os.environ.get('MONGODB_ENABLED', False)
DEVICES = []

if MONGODB_ENABLED:
    client = pymongo.MongoClient(os.environ['MONGODB_URI'])
    db = client['status-insights']
    collection = db['devices']

    def update():
        global DEVICES
        device_list = []
        try:
            for device in collection.find():
                device_list.append(device)
            DEVICES = device_list
        except Exception as e:
            print(f"Failed to update devices: {e}")
            DEVICES = []
    update()

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
        update()
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
                update()
                return
        raise RuntimeError(f"Device with id {device_id} not found.")
    else:
        for index, device in enumerate(DEVICES):
            if device['id'] == device_id:
                DEVICES.pop(index)
                print(f"Popped {index}: {device}.")
                return
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