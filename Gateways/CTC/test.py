# this file just for test

import json
from functions import conn
import asyncio
from commands import (
    get_dynamic_sensors,
    subscribe_to_changes,
    unsubscribe_from_changes,
    get_connected_dynamic_sensors,
    take_dynamic_vibration_reading,
    take_dynamic_temperature_reading,
    take_dynamic_battery_reading,
    get_dynamic_vibration_records,
    get_dynamic_temperature_records,
    get_dynamic_battery_records,
)
import websockets


async def main():
    ws = None
    try:
        ws = await conn("ws://192.168.13.2:5000")
        result = await get_dynamic_battery_records(ws)

        # TODO: use json.dumps to print the result in a pretty format
        print(json.dumps(result, indent=4))

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
