import asyncio
import websockets

async def test():
    uri = "ws://localhost:8000/ws/candles/BTC-USD"
    async with websockets.connect(uri) as ws:
        print("Connected. Waiting for candles...")
        async for message in ws:
            print(message)

asyncio.run(test())