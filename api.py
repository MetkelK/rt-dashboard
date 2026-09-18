import json
import asyncio
import redis
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from collections import defaultdict
import time

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ws_connections = defaultdict(list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5175",
        "https://d1qhsrzkm3vw60.cloudfront.net"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)))


@app.get("/api/candles/{symbol}")
@limiter.limit("30/minute")
def get_candles(request: Request, symbol: str, limit: int = 200):
    redis_key = f"candles:{symbol.replace('-', '/')}"
    raw_candles = r.zrange(redis_key, -limit, -1)
    candles = [json.loads(c) for c in raw_candles]
    return {"symbol": symbol, "candles": candles}


@app.websocket("/ws/candles/{symbol}")
async def candle_stream(websocket: WebSocket, symbol: str):
    client_ip = websocket.client.host
    now = time.time()
    ws_connections[client_ip] = [t for t in ws_connections[client_ip] if now - t < 60]
    if len(ws_connections[client_ip]) >= 10:
        await websocket.close(code=1008)
        return
    ws_connections[client_ip].append(now)

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