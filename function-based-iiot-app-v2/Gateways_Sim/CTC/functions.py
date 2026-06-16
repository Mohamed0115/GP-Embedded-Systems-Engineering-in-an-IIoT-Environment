import asyncio

async def send(ws, commands):
    print(f"MOCK sent: {commands}")

async def receive(ws):
    return {"Status": "OK", "Message": "MOCK_RESPONSE"}

class MockWS:
    async def close(self):
        print("MOCK Connection closed")

async def conn(url):
    print(f"MOCK Connected to {url}")
    return MockWS()

async def close(ws):
    print("MOCK standalone connection closed")
