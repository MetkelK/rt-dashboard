import CandleChart from "./CandleChart";

function App() {
  const stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"];

  return (
    <div style={{ padding: "1rem" }}>
      <h1>RT Dashboard</h1>

      <div style={{ marginBottom: "2rem" }}>
        <CandleChart symbol="BTC-USD" height="50vh" />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "1.5rem",
        }}
      >
        {stocks.map((symbol) => (
          <CandleChart key={symbol} symbol={symbol} height={200} />
        ))}
      </div>
    </div>
  );
}

export default App;
