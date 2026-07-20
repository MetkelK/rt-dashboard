import asyncio
import json
import websockets
from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': 'localhost:9092'})


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")


def normalize_kraken(candle):
    return {
        "symbol": candle["symbol"],
        "timestamp": candle["interval_begin"],
        "open": candle["open"],
        "high": candle["high"],
        "low": candle["low"],
        "close": candle["close"],
        "volume": candle["volume"],
        "source": "kraken",
    }


async def ingest_kraken():
    uri = "wss://ws.kraken.com/v2"

    while True:  # reconnect loop
        try:
            async with websockets.connect(uri) as ws:
                subscribe_msg = {
                    "method": "subscribe",
                    "params": {"channel": "ohlc", "symbol": ["BTC/USD"], "interval": 1}
                }
                await ws.send(json.dumps(subscribe_msg))

                async for raw_msg in ws:
                    msg = json.loads(raw_msg)

                    if msg.get("channel") not in ("ohlc",):
                        continue

                    for candle in msg["data"]:
                        normalized = normalize_kraken(candle)
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


asyncio.run(ingest_kraken())