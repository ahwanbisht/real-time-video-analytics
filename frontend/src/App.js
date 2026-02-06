import React, { useEffect, useState } from "react";
import "./App.css";

import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";

import { Line } from "react-chartjs-2";

// Register chart components
ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

// Component starts AFTER imports
function App() {
  const [page, setPage] = useState("live");
  const [historyData, setHistoryData] = useState(null);

  const [stats, setStats] = useState({
    count_in: 0,
    count_out: 0,
    current_inside: 0,
    alerts: [],
  });

  const [history, setHistory] = useState([]);

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStats(data);

      setHistory((prev) => {
        const updated = [...prev, data.current_inside];
        if (updated.length > 20) updated.shift();
        return updated;
      });
    };

    return () => ws.close();
  }, []);

  return (
    <div className="app">

      <nav className="navbar">
        <h2>Retail AI Analytics</h2>
        <div>
          <button onClick={() => setPage("live")}>Live</button>
          <button onClick={() => {
            setPage("history");
            fetch("http://127.0.0.1:8000/history")
              .then(res => res.json())
              .then(data => setHistoryData(data));
          }}>
            Analytics
          </button>
        </div>
      </nav>

      <div className="container">
      <div style={{ marginBottom: "20px" }}>
      <button onClick={() => setPage("live")}>Live Dashboard</button>
      <button onClick={() => {
        setPage("history");
        fetch("http://127.0.0.1:8000/history")
          .then(res => res.json())
          .then(data => setHistoryData(data));
      }}>
        Historical Analytics
      </button>
    </div>
      {page === "live" && (
      <>
        <h1>Retail Analytics Dashboard</h1>

        <div className="card" style={{ width: "600px" }}>
        <h3>System Status</h3>

        <p>
          AI Engine: 
          <span className={`status ${stats.system_status?.ai}`}>
            {stats.system_status?.ai}
          </span>
        </p>

        <p>
          Database: 
          <span className={`status ${stats.system_status?.database}`}>
            {stats.system_status?.database}
          </span>
        </p>
      </div>

        <div className="card" style={{ width: "700px" }}>
          <h3>Live Camera Feed</h3>
          <img
            src="http://127.0.0.1:8000/video"
            alt="Live Camera"
            style={{ width: "100%", borderRadius: "10px" }}
          />
        </div>

        <div className="card">
          <h2>Current Occupancy</h2>
          <p>{stats.current_inside}</p>
        </div>

        <div className="card-row">
          <div className="card">
            <h3>Total Entered</h3>
            <p>{stats.count_in}</p>
          </div>

          <div className="card">
            <h3>Total Exited</h3>
            <p>{stats.count_out}</p>
          </div>
        </div>

        <div className="card">
          <h3>Live Alerts</h3>
          {stats.alerts && stats.alerts.length > 0 ? (
            stats.alerts.map((alert, index) => (
              <div key={index} className={`alert ${alert.type}`}>
                {alert.message}
              </div>
            ))
          ) : (
            <p>No alerts</p>
          )}
        </div>

        <div className="card" style={{ width: "600px" }}>
          <h3>Live Occupancy Trend</h3>
          <Line
            data={{
              labels: history.map((_, index) => index + 1),
              datasets: [
                {
                  label: "Current Inside",
                  data: history,
                  borderColor: "blue",
                  fill: false,
                },
              ],
            }}
          />
        </div>
      </>)}

      {page === "history" && historyData && (
        <div>
          <div className="card">
            <h2>Historical Analytics</h2>
            <p>Total Customers: {historyData.total_customers}</p>
            <p>Average Dwell Time: {historyData.avg_dwell}</p>
            <p>Max Dwell Time: {historyData.max_dwell}</p>
          </div>

          <div className="card" style={{ width: "600px" }}>
            <h3>Dwell Time Trend</h3>
            <Line
              data={{
                labels: historyData.dwell_history.map((_, i) => i + 1),
                datasets: [
                  {
                    label: "Dwell Time (seconds)",
                    data: historyData.dwell_history,
                    borderColor: "green",
                    fill: false,
                  },
                ],
              }}
            />
          </div>

          <div className="card" style={{ width: "600px" }}>
            <h3>Customer Growth Trend</h3>
            <Line
              data={{
                labels: historyData.customer_trend.map((_, i) => i + 1),
                datasets: [
                  {
                    label: "Total Customers",
                    data: historyData.customer_trend,
                    borderColor: "purple",
                    fill: false,
                  },
                ],
              }}
            />
          </div>
        </div>
      )}

    </div>
  </div>
  );
}

export default App;
