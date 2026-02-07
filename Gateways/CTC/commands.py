from functions import send,receive
#import asyncio


#--------------------SEND COMMANDS
async def subscribe_to_changes(ws):
    command = {
        "Type": "POST_SUB_CHANGES",
        "From": "UI",
        "To": "SERV",
        "Data": {}
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def unsubscribe_from_changes(ws):
    command = {
        "Type": "POST_UNSUB_CHANGES",
        "From": "UI",
        "To": "SERV",
        "Data": {}
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def get_dynamic_sensors(ws, serials=None):
    if serials is None:
        serials = []

    command = {
        "Type": "GET_DYN",
        "From": "UI",
        "To": "SERV",
        "Data": {"Serials": serials}
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def get_connected_dynamic_sensors(ws):
    command = {
        "Type": "GET_DYN_CONNECTED",
        "From": "UI",
        "To": "SERV",
        "Data": {}
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def take_dynamic_vibration_reading(ws, serial: int):
    command = {
        "Type": "TAKE_DYN_READING",
        "From": "UI",
        "To": "SERV",
        "Data": {"Serial": serial}
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def take_dynamic_temperature_reading(ws, serial: int):
    command = {
        "Type": "TAKE_DYN_TEMP",
        "From": "UI",
        "To": "SERV",
        "Data": {"Serial": serial}
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def take_dynamic_battery_reading(ws, serial: int):
    command = {
        "Type": "TAKE_DYN_BATT",
        "From": "UI",
        "To": "SERV",
        "Data": {"Serial": serial}
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def get_dynamic_vibration_records(ws, serials=None, start=None, end=None, max_records=25):
    data = {"Max": max_records}
    if serials is not None:
        data["Serials"] = serials
    if start:
        data["Start"] = start
    if end:
        data["End"] = end

    command = {
        "Type": "GET_DYN_READINGS",
        "From": "UI",
        "To": "SERV",
        "Data": data
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def get_dynamic_temperature_records(ws, serials=None, start=None, end=None, max_records=25):
    data = {"Max": max_records}
    if serials is not None:
        data["Serials"] = serials
    if start:
        data["Start"] = start
    if end:
        data["End"] = end

    command = {
        "Type": "GET_DYN_TEMPS",
        "From": "UI",
        "To": "SERV",
        "Data": data
    }
    await send(ws, command)
    return await receive(ws)
#----------
async def get_dynamic_battery_records(ws, serials=None, start=None, end=None, max_records=25):
    data = {"Max": max_records}
    if serials is not None:
        data["Serials"] = serials
    if start:
        data["Start"] = start
    if end:
        data["End"] = end

    command = {
        "Type": "GET_DYN_BATTS",
        "From": "UI",
        "To": "SERV",
        "Data": data
    }
    await send(ws, command)
    return await receive(ws)


