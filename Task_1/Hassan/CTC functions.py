# this code for CTC gateway and work well
# it is type using methdollogy functions
# there development to this code at other file connection and login happen
# from conn function

import asyncio
import websockets
import json

# Login message
login = {
    "Type": "POST_LOGIN",
    "From": "UI",
    "Target": "SERV",
    "Data": {
        "Email":"hassanmagdy600@gmail.com",
        "Password":"Asdasdasd3@",
    },
}

# Message X
X = {
    "Type": "GET_DYN",
    "From": "UI",
    "To": "SERV",
    "Data": {
        "Serials": []  # replace with your actual serial numbers
    },
}

# Function to connect
async def conn(url):
    ws = await websockets.connect(url)
    print("Connected")
    return ws

# Function to send
async def send(ws,request):
    # I don't know yet which line is better, i think it will be the second one
    request_json = await ws.send(json.dumps(request))
    print(request_json)
    # no actually the code will not run if you use mext line
    #request_json = json.dumps(await ws.send(request))

    print("Request sent:", request)
    return request_json

# Function to Receive
async def receive(ws):
    message = await ws.recv()
    return json.loads(message)

async def main():
    url = "ws://"+input("Enter URL: ")
    ws = None
    # I use try and except here due there many potential problems may happen at communications
    try:

        ws = await conn(url)

        await send(ws,login)
        print("your_Login  :", login)
        Login_Result = await receive(ws)
        print("Login Result:", Login_Result)

        await send (ws,X)
        print("your_massage:", X)
        Server_Replied = await receive(ws)
        print("Server_Replied:", Server_Replied)
        print("to check parsing:", Server_Replied["From"])

    except websockets.exceptions.ConnectionClosedError as e:
        print("Connection closed unexpectedly")
    except Exception as e:
        print("Error:", e)

    finally:
        if ws:
            await ws.close()
            print("Connection closed cleanly")

if __name__ == "__main__":
    asyncio.run(main())
