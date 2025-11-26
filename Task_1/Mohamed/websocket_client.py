
import asyncio
import websockets
import json  
import signal #🔴

URI = "ws://localhost:8765"  # Server address 🔴
CLIENT_ID = "Mido_PC_Client"  # For identification 

async def send_loop(websocket):
    while True:
        message = {"topic": "/mido/hello", "msg": "Hello World"}
        await websocket.send(json.dumps(message)) #🔴
        print(f"🔵 Sent: {message['msg']} → {message['topic']}")
        await asyncio.sleep(5)  # Every 5 seconds

async def receive_loop(websocket):
    async for message in websocket:
        try:
            data = json.loads(message) #🔴
            print(f"🟢 Received on {data.get('topic', 'unknown')} → {data.get('msg', 'Unknown')}")
        except json.JSONDecodeError:  #🔴
            print(f"Invalid response: {message}")

async def main():
    print("Connecting....")
    async with websockets.connect(URI, ping_interval=None, ping_timeout=None) as websocket:  #🔴
        print("✅ Connected to server!")
        
        # Start send loop in background (like publisher thread)
        send_task = asyncio.create_task(send_loop(websocket)) #🔴
        
        # Receive loop (like on_message)
        await receive_loop(websocket)  #🔴
        
        # Cleanup (won't reach here unless disconnected)
        send_task.cancel() #🔴

# Handle Ctrl+C shutdown
def shutdown():
    print("\nDone")
    # No explicit disconnect needed; async with handles it

signal.signal(signal.SIGINT, lambda s, f: shutdown()) #🔴

# Run client
asyncio.run(main()) #🔴