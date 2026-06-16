import random
import datetime

async def get_dynamic_battery_records(ws, serials=None, start=None, end=None, max_records=25):
    return {"Data": [{"Serial": s, "Battery": random.uniform(3.5, 4.2)} for s in (serials or [101])]}
    
async def take_dynamic_vibration_reading(ws, serial: int):
    return {"Data": [{"Serial": serial, "Vibration": random.uniform(0.1, 0.5)}]}
    
async def take_dynamic_temperature_reading(ws, serial: int):
    return {"Data": [{"Serial": serial, "Temperature": random.uniform(25.0, 45.0)}]}

async def subscribe_to_changes(ws):
    return {"Type": "ACK", "Message": "Subscribed"}

async def unsubscribe_from_changes(ws):
    return {"Type": "ACK", "Message": "Unsubscribed"}

async def get_connected_dynamic_sensors(ws):
    return {"Type": "RTN_DYN", "Data": [{"Serial": 30000033, "PartNum": "WS300", "Connected": 1}]}

async def get_dynamic_vibration_records(ws, serials=None, start=None, end=None, max_records=25):
    return {"Data": [{"Serial": s, "Vibration": random.uniform(0.1, 0.5)} for s in (serials or [101])]}
