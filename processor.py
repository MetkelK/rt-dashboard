import json
import redis
from confluent_kafka import Consumer

consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'candle-processor',
    'auto.offset.reset': 'earliest',
})
consumer.subscribe(['market-ticks'])

r = redis.Redis()

print("Listening for ticks...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        candle = json.loads(msg.value().decode('utf-8'))
        symbol = candle["symbol"]
        redis_key = f"candles:{symbol}"

        # Score by timestamp (converted to a unix float) so candles stay sorted
        import datetime
        ts = datetime.datetime.fromisoformat(candle["timestamp"].replace("Z", "+00:00"))
        score = ts.timestamp()

        # Remove any existing entry with the same timestamp before adding —
        # this is what handles Kraken sending repeated updates for the same
        # in-progress minute, so we always keep just the latest version
        existing = r.zrangebyscore(redis_key, score, score)
        if existing:
            r.zrem(redis_key, *existing)

        r.zadd(redis_key, {json.dumps(candle): score})
        r.zremrangebyrank(redis_key, 0, -1001)  # keep only the most recent 1000

        print(f"Stored candle for {symbol} at {candle['timestamp']}")

except KeyboardInterrupt:
    pass
finally:
    consumer.close()