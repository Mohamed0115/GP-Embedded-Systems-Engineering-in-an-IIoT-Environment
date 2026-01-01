# this code for CTC gateway and work well
# it is type using methdollogy functions
# this code done connection and login from one function conn
import asyncio
import websockets
import json

#------------------
import commands
#------------------


# Login message
login = {
    "Type": "POST_LOGIN",
    "From": "UI",
    "Target": "SERV",
    "Data": {
        "Email":input("Enter your email: "),
        "Password":input("Enter password: "),
    },
}

# # Message X
# X = {
#     "Type": "GET_DYN",
#     "From": "UI",
#     "To": "SERV",
#     "Data": {
#         "Serials": []  # replace with your actual serial numbers
#     },
# }



# Function to send
async def send(ws,request):
    request_json = await ws.send(json.dumps(request))
    print("Request sent:", request)
    return request_json

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
    Login_Result = await receive(ws)
    print("Login Result:", Login_Result)
    return ws

async def main():

    url = "ws://"+input("Enter URL: ")
    ws = None
    # I use try and except here due there many potential problems may happen at communcatios
    try:

        ws = await conn(url)

        X = command
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
