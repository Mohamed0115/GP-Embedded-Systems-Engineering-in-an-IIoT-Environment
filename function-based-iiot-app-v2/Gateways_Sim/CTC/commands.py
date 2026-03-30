import random
import datetime

async def get_dynamic_battery_records(ws, serials=None, start=None, end=None, max_records=25):
    return {"Data": [{"Serial": s, "Battery": random.uniform(3.5, 4.2)} for s in (serials or [101])]}
    
async def take_dynamic_vibration_reading(ws, serial: int):
    return {"Data": [{"Serial": serial, "Vibration": random.uniform(0.1, 0.5)}]}
    
async def take_dynamic_temperature_reading(ws, serial: int):
    return {"Data": [{"Serial": serial, "Temperature": random.uniform(25.0, 45.0)}]}
