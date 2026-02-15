import asyncio
from commands_ip import ip, excute_command
from parameters_con import parameters
from csv_des import take_A_decision, csvf
from CDSR import connect, disconnect


async def main():
    port = 8020
    # timeout = 15
    reader = None
    writer = None
    intetvals_second = 5

    used_ip = ip() or "192.168.13.10"
    used_parameters = parameters()
    try:
        reader, writer = await connect(used_ip, port)
        x = await excute_command(reader, writer, "FV?")
        print(x)
        x = await excute_command(reader, writer, "DS?")
        print(x)
        x = await excute_command(reader, writer, used_parameters["commands"])
        print(x)
        # while True:
        #     x = await excute_command(reader, writer, "AQ")
        #     print(x)
        #     data = await excute_command(reader, writer, "BD?", used_parameters["TL"])
        #     csvf(data)
        #     await take_A_decision(reader, writer)
        await asyncio.sleep(intetvals_second)
    except KeyboardInterrupt:
        print("( ctrl+c ) stops the code.")
    except Exception as e:
        print(f"Error :{e}")
    finally:
        await disconnect(writer)
        print("Disconnected successfully")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Disconnected")
