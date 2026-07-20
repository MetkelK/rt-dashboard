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
  const res = await fetch(`http://localhost:8000/api/candles/${symbol}`);
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

function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);
  const queryClient = useQueryClient();
  const symbol = "BTC-USD";

  const { data, isLoading, error } = useQuery({
    queryKey: ["candles", symbol],
    queryFn: () => fetchCandles(symbol),
    refetchInterval: false,
  });

  // Build/update the chart whenever the underlying data changes
  useEffect(() => {
    if (!data || !canvasRef.current) return;

    const chartData = data.candles.map(toChartPoint);

    if (!chartRef.current) {
      const config: ChartConfiguration = {
        type: "candlestick" as any,
        data: {
          datasets: [
            {
              label: data.symbol,
              data: chartData as any,
            },
          ],
        },
        options: {
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

  // Open the WebSocket once, independent of React Query's fetch/cache cycle
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/candles/${symbol}`);

    ws.onmessage = (event) => {
      const newCandle: Candle = JSON.parse(event.data);

      // Merge the new candle into TanStack Query's cache so both the
      // cache and the chart stay in sync with the live data
      queryClient.setQueryData<CandlesResponse>(["candles", symbol], (old) => {
        if (!old) return old;
        const existingIndex = old.candles.findIndex(
          (c) => c.timestamp === newCandle.timestamp,
        );
        const updatedCandles = [...old.candles];
        if (existingIndex >= 0) {
          updatedCandles[existingIndex] = newCandle; // same minute, replace
        } else {
          updatedCandles.push(newCandle); // new minute, append
        }
        return { ...old, candles: updatedCandles };
      });
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [queryClient]);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading candles</div>;

  return (
    <div>
      <h1>RT Dashboard</h1>
      <canvas ref={canvasRef} width={800} height={400}></canvas>
    </div>
  );
}

export default App;
