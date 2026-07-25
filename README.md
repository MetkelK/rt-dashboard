# rt-dashboard

A real-time financial data streaming pipeline and dashboard, built as a term project for Big Data course 3252.

Live market data from Kraken (crypto) and Alpaca (equities) is ingested, published to Kafka, aggregated into OHLC candles by a stream processor, stored in Redis, and served to a React dashboard over REST and WebSocket.

## Architecture

```
Kraken WebSocket        Alpaca WebSocket
       │                      │
       ▼                      ▼
Ingestion service      Ingestion service
       \                     /
        ▼                   ▼
        Redpanda (Kafka) — market-ticks
                  │
                  ▼
          Stream processor
                  │
                  ▼
                Redis
                  │
                  ▼
         FastAPI backend
                  │
                  ▼
          React dashboard
```

## Prerequisites

- Docker Desktop
- conda (conda-forge channel configured)
- Node.js + npm

### Installing the prerequisites

**Docker Desktop** — download and install from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/). On Apple Silicon Macs, make sure you get the Apple Silicon (ARM64) build. After installing, open the Docker Desktop app once to finish setup before using the CLI.

**conda** — install Miniconda (a minimal conda installer) from [docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html), choosing the installer for your OS/architecture. Verify it installed correctly:

```bash
conda --version
```

Add the conda-forge channel if it isn't already configured:

```bash
conda config --add channels conda-forge
```

**Node.js + npm** — download the LTS installer from [nodejs.org](https://nodejs.org/), or install via a version manager (e.g. [nvm](https://github.com/nvm-sh/nvm)):

```bash
nvm install --lts
```

Verify:

```bash
node --version
npm --version
```

## 1. Start local infrastructure

```bash
docker compose up -d
```

This starts Redpanda (Kafka-compatible broker) on port 9092 and Redis on port 6379.

Create the Kafka topic:

```bash
docker exec -it redpanda rpk topic create market-ticks -p 4
```

Verify both are running:

```bash
docker exec -it redis redis-cli ping        # expect PONG
docker exec -it redpanda rpk topic list     # expect market-ticks listed
```

## 2. Set up the Python environment

```bash
conda create -n rt-dashboard python=3.11
conda activate rt-dashboard
conda install -c conda-forge fastapi uvicorn redis-py
pip install confluent-kafka websockets python-dotenv
```

## 3. Configure environment variables

Create a `.env` file in the project root with your Alpaca API credentials:

```
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
```

Get free paper-trading API keys at [app.alpaca.markets](https://app.alpaca.markets). Kraken's feed requires no credentials.

`.env` is gitignored and should never be committed.

## 4. Run the pipeline

Each of these runs in its own terminal, with the `rt-dashboard` conda environment active:

```bash
python ingest.py            # Kraken (crypto) ingestion
python ingest_alpaca.py      # Alpaca (equities) ingestion — live data only during US market hours, ~9:30am–4:00pm ET weekdays
python processor.py          # stream processor: Kafka → Redis
uvicorn api:app --reload --reload-exclude "ingest*.py" --reload-exclude "processor.py" --port 8000
```

The `--reload-exclude` flags keep the API server from restarting (and dropping active WebSocket connections) when the ingestion or processor scripts are edited.

## 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`). If Vite picks a different port, update `allow_origins` in `api.py`'s CORS configuration to match.

## Verifying it's working

```bash
docker exec -it redpanda rpk topic consume market-ticks   # see raw ticks flowing through Kafka
docker exec -it redis redis-cli zrange candles:BTC/USD 0 -1  # see stored candles
curl "http://localhost:8000/api/candles/BTC-USD"            # confirm the REST endpoint
```

## Notes

- Everything runs locally and free — no paid services, no cloud deployment required.
- Kraken's feed is public and available 24/7. Alpaca's equities feed only produces data during regular US market hours.
- Redis retains a rolling window of the most recent 1,000 candles per symbol; it is a cache, not permanent storage.
