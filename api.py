import json
import asyncio
import redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis()


@app.get("/api/candles/{symbol}")
def get_candles(symbol: str, limit: int = 200):
    redis_key = f"candles:{symbol.replace('-', '/')}"
    raw_candles = r.zrange(redis_key, -limit, -1)
    candles = [json.loads(c) for c in raw_candles]
    return {"symbol": symbol, "candles": candles}


@app.websocket("/ws/candles/{symbol}")
async def candle_stream(websocket: WebSocket, symbol: str):
    await websocket.accept()
    redis_key = f"candles:{symbol.replace('-', '/')}"
    last_sent = None

    try:
        while True:
            latest = r.zrange(redis_key, -1, -1)
            if latest:
                candle_json = latest[0].decode('utf-8')
                if candle_json != last_sent:
                    await websocket.send_text(candle_json)
                    last_sent = candle_json
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print(f"Client disconnected from {symbol} stream")