import asyncio
from .CDSR import send, receive_data, receive_normal

def ip():
    # Helper mimic
    return "192.168.1.100"

async def excute_command(reader, writer, command):
    await send(writer, command)
    resp = await receive_normal(reader)
    return resp
    
async def excute_data_command(reader, writer, command, TL=0):
    await send(writer, command)
    resp = await receive_data(reader, command, TL)
    return resp
