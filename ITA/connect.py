import asyncio

async def connect(ip, port=8020, timeout=5):
    """
    Asynchronously connect to the ITA-110 device.
    Returns reader and writer streams.
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        return reader, writer
    except asyncio.TimeoutError:
        raise ConnectionError("Connection timeout")
    except Exception as e:
        raise ConnectionError(f"Connection failed: {e}")