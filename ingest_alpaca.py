import asyncio
import json
import os
import websockets
from dotenv import load_dotenv
from confluent_kafka import Producer

load_dotenv()

API_KEY = os.environ["ALPACA_API_KEY"]
SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

producer = Producer({'bootstrap.servers': 'localhost:9092'})


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")


def normalize_alpaca(bar):
    """Map an Alpaca bar message into our internal schema."""
    return {
        "symbol": bar["S"],
        "timestamp": bar["t"],
        "open": bar["o"],
        "high": bar["h"],
        "low": bar["l"],
        "close": bar["c"],
        "volume": bar["v"],
        "source": "alpaca",
    }


async def ingest_alpaca():
    uri = "wss://stream.data.alpaca.markets/v2/iex"

    while True:  # reconnect loop
        try:
            async with websockets.connect(uri) as ws:
                # 1. Wait for the initial connection confirmation
                await ws.recv()

                # 2. Authenticate
                auth_msg = {
                    "action": "auth",
                    "key": API_KEY,
                    "secret": SECRET_KEY,
                }
                await ws.send(json.dumps(auth_msg))
                auth_response = await ws.recv()
                print(f"Auth response: {auth_response}")

                # 3. Subscribe to minute bars for a symbol
                subscribe_msg = {
                    "action": "subscribe",
                    "bars": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
                }
                await ws.send(json.dumps(subscribe_msg))

                async for raw_msg in ws:
                    messages = json.loads(raw_msg)

                    # Alpaca sends a list of message objects, each with a "T" type field
                    for msg in messages:
                        if msg.get("T") != "b":  # only interested in bar ("b") messages
                            continue

                        normalized = normalize_alpaca(msg)
                        producer.produce(
                            topic="market-ticks",
                            key=normalized["symbol"],
                            value=json.dumps(normalized).encode("utf-8"),
                            callback=delivery_report,
                        )
                        producer.poll(0)
                        print(f"Published: {normalized}")

        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed ({e}), reconnecting in 3 seconds...")
            await asyncio.sleep(3)


asyncio.run(ingest_alpaca())