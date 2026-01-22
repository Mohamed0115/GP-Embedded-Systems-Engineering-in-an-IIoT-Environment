import asyncio
from connect import connect
from disconnect import disconnect
from send import send
from receiver import receive

async def send_custom():
    ip = input("Enter ITA-110 IP address: ") or '192.168.13.10'
    port = 8020
    timeout = 30
    
    custom_cmd = input("Enter command to send (e.g., 'DT 24/12/25'): ")
    if not custom_cmd:
        print("No command entered.")
        return
    
    reader = None
    writer = None
    try:
        reader, writer = await connect(ip, port, timeout)
        print("Connected for sending.")
        
        print(f"Sending: {custom_cmd}")
        await send(writer, custom_cmd)
        resp = await receive(reader, timeout=timeout)
        print(f"Response: {resp['response'] if resp['type'] == 'ascii' else resp}")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await disconnect(writer)
        print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(send_custom())