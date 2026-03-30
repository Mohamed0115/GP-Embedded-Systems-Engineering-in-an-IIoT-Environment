import asyncio
import re
from CDSR import send , receive_data , receive_normal

def ip():
    ip = input("enter ip") or '192.168.13.10'
    if  re.match(r'^(\d{1,3}\.){3}\d{1,3}$',ip) or not any(int(part) > 255 for part in ip.split('.')) :
        return ip
    raise ValueError("Not a valid ip")
         

async def excute_command(reader , writer , command):
    await send(writer,command)
    resp = await receive_normal(reader)
    if 'NA' in resp['response'] or 'ER' in resp['response'] :
        raise ValueError(f"Error with {command} command as the response is {resp['response']}")
    return resp

async def excute_data_command(reader , writer , command, TL = 0):
    await send(writer,command)
    resp = await receive_data(reader,command,TL)
    if 'NA' in resp['response'] or 'ER' in resp['response'] :
        raise ValueError(f"Error with {command} command as the response is {resp['response']}")
    return resp