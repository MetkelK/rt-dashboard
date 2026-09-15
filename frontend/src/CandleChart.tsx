import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import {
  Chart,
  TimeScale,
  LinearScale,
  Tooltip,
  Legend,
  type ChartConfiguration,
} from "chart.js";
import "chartjs-adapter-date-fns";
import {
  CandlestickController,
  CandlestickElement,
} from "chartjs-chart-financial";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws");

Chart.register(
  CandlestickController,
  CandlestickElement,
  TimeScale,
  LinearScale,
  Tooltip,
  Legend,
);

interface Candle {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
}

interface CandlesResponse {
  symbol: string;
  candles: Candle[];
}

async function fetchCandles(symbol: string): Promise<CandlesResponse> {
  const res = await fetch(`${API_URL}/api/candles/${symbol}`);
  if (!res.ok) throw new Error("Failed to fetch candles");
  return res.json();
}

function toChartPoint(c: Candle) {
  return {
    x: new Date(c.timestamp).getTime(),
    o: c.open,
    h: c.high,
    l: c.low,
    c: c.close,
  };
}

interface CandleChartProps {
  symbol: string;
  height?: number | string;
}
function CandleChart({ symbol, height = 250 }: CandleChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["candles", symbol],
    queryFn: () => fetchCandles(symbol),
    refetchInterval: false,
  });

  useEffect(() => {
    if (!data || !canvasRef.current) return;

    const chartData = data.candles.map(toChartPoint);

    if (!chartRef.current) {
      const config: ChartConfiguration = {
        type: "candlestick" as any,
        data: {
          datasets: [{ label: data.symbol, data: chartData as any }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false, // let it fill the container's actual height, not a fixed ratio
          scales: {
            x: { type: "time", time: { unit: "minute" } },
          },
        },
      };
      chartRef.current = new Chart(canvasRef.current, config);
    } else {
      chartRef.current.data.datasets[0].data = chartData as any;
      chartRef.current.update();
    }
  }, [data]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/candles/${symbol}`);

    ws.onmessage = (event) => {
      const newCandle: Candle = JSON.parse(event.data);
      queryClient.setQueryData<CandlesResponse>(["candles", symbol], (old) => {
        if (!old) return old;
        const existingIndex = old.candles.findIndex(
          (c) => c.timestamp === newCandle.timestamp,
        );
        const updatedCandles = [...old.candles];
        if (existingIndex >= 0) {
          updatedCandles[existingIndex] = newCandle;
        } else {
          updatedCandles.push(newCandle);
        }
        return { ...old, candles: updatedCandles };
      });
    };

    ws.onerror = (err) => console.error(`WebSocket error (${symbol}):`, err);

    return () => {
      if (ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, [symbol, queryClient]);

  if (isLoading) return <div>Loading {symbol}...</div>;
  if (error) return <div>Error loading {symbol}</div>;

  return (
    <div>
      <h3>{symbol}</h3>
      <div style={{ height, position: "relative" }}>
        <canvas ref={canvasRef}></canvas>
      </div>
    </div>
  );
}

export default CandleChart;
