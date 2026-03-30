import asyncio
import random

async def connect(ip, port):
    print(f"MOCK Connected to ITA at {ip}:{port}")
    return "mock_reader", "mock_writer"
    
async def disconnect(writer):
    print("MOCK Disconnected ITA")
    
async def receive_normal(reader):
    return {"response": ["OK"]}
    
async def receive_data(reader, command, TL):
    # ITA simulator providing mocked arrays mimicking actual CDSR dict schema
    samples = [random.randint(-100, 100) for _ in range(TL)]
    return {
        "response": samples,
        "status": 0,
        "range_val ": 1,
        "schema ": 2,
        "runnig_speed ": 1800.0
    }

async def send(writer, command):
    pass
