import asyncio

async def send(ws, commands):
    print(f"MOCK sent: {commands}")

async def receive(ws):
    return {"Status": "OK", "Message": "MOCK_RESPONSE"}

async def conn(url):
    print(f"MOCK Connected to {url}")
    return "mock_ws"

async def close(ws):
    print("MOCK Connection closed")
