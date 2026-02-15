import websockets
import json
import asyncio

# we will remove login email and password and make it with input, it is just for trial
login = {
    "Type": "POST_LOGIN",
    "From": "UI",
    "Target": "SERV",
    "Data": {"Email": "hassanmagdy600@gmail.com", "Password": "Asdasdasd3@"},
}


async def send(ws, commands):
    await ws.send(json.dumps(commands))
    print("Request sent:", commands)


# Function to Receive
async def receive(ws):
    message = json.loads(await ws.recv())
    return message


# Function to connect
async def conn(url):
    ws = await websockets.connect(url)
    print("Connected")
    await send(ws, login)
    print("your_Login  :", login)
    login_result = await receive(ws)
    print("Login Result:", login_result)
    return ws
