import asyncio
import json
import struct
from parameters_con import parameters


async def connect(ip, port):  # try if there is no exception
    reader, writer = await asyncio.open_connection(ip, port)
    return reader, writer


async def disconnect(writer):
    if writer:
        writer.close()
        await writer.wait_closed()


async def send(writer, command):
    full = command + "\r"
    writer.write(full.encode("ascii"))
    await writer.drain()


# async def receive(reader, command, TL):

#     data = b""
#     if command in ["BD?", "BH?"]:
#         sample_size = 4
#         data_len = TL * sample_size if command == "BD?" else 0
#         data_len += 16

#     try:
#         while True:
#             chunk = await asyncio.wait_for(reader.read(9000), timeout=1000)
#             data += chunk
#             if command in ["BD?", "BH?"]:
#                 if len(data) >= data_len:
#                     break
#             if b"\r" in data:
#                 break
#     except asyncio.TimeoutError:
#         raise ValueError("Receive timeout")
#     except Exception as e:
#         raise UnicodeDecodeError("hi")

#     if command in ["BD?", "BH?"]:
#         prefix = command[0:2].encode() + b"="
#         if data.startswith(prefix):
#             header = data[3:16]
#             binary_data = data[16 : data_len - 16]
#             (
#                 status,
#                 range_val,
#                 schema,
#                 channel,
#                 format_val,
#                 trace_length,
#                 running_speed,
#             ) = struct.unpack(">BBBBBIf", header)
#             samples = [
#                 struct.unpack(">i", binary_data[i : i + 4])[0]
#                 for i in range(0, len(binary_data), 4)
#             ]
#             return {
#                 "response": samples,
#                 "status": status,
#                 "range_val ": range_val,
#                 "schema ": schema,
#                 "runnig_speed ": running_speed,
#             }
#         else:
#             response = data.decode("ascii").strip()
#             return {"response": response}

#     else:
#         response = data.decode("ascii").strip()
#         return {"response": response}


# TODO: make a general receive function
# TODO: you make a spesial receive function for BD? and BH? that can handle the binary data and the header, and return a dictionary with the relevant information


async def receive(reader):
    data = b""
    timeout = 10
    while True:
        try:
            chunk = await asyncio.wait_for(reader.readuntil(b"\r"), timeout)
            if not chunk:
                break
            data += chunk

        except asyncio.TimeoutError:
            break
        except Exception as e:
            # TODO: relevant 'hi' for debugging, but not for the user, so we raise a generic error
            raise UnicodeDecodeError("hi")

    text = data.decode("ascii")
    messages = text.split("\r")  # split by carriage return
    messages = [m for m in messages if m]  # remove empty strings
    return messages
