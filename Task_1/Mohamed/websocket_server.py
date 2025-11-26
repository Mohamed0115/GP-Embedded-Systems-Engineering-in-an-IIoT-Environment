# Run this first: python websocket_server.py
# It listens for clients, receives messages (like on_message), prints them,
# and can send back if needed. Handles connect/disconnect.

import asyncio     #wait for output
import websockets
import json  #tranform to dic

PORT = 8765  
connected_clients = set()   

async def handler(websocket):  #when there is a new connection
    print(f"✅ Client connected from {websocket.remote_address}")
    connected_clients.add(websocket)
    
    try:
        async for message in websocket:   #when recive any message [listener]
            try:
                data = json.loads(message) #🔵 transfer data to dict.  # Assume JSON like {"topic": "/mido/control", "msg": "Your message"}
                print(f"🟢 Received message on {data.get('topic', 'unknown')} → {data['msg']}")
                
            except json.JSONDecodeError:
                print(f"Invalid message: {message}")
    
    except websockets.exceptions.ConnectionClosed:
        print(f"Client {websocket.remote_address} disconnected")
    
    finally:
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "localhost", PORT, ping_interval=None, ping_timeout=None):  #run & for each client run the fun/
        print(f"WebSocket server listening on :{PORT}")
        await asyncio.Future()  # Run forever

# Run server (Ctrl+C to stop)
asyncio.run(main())  ## run event loop & run main