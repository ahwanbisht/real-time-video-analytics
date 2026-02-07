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

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

function App() {
  const [stats, setStats] = useState({
    count_in: 0,
    count_out: 0,
    current_inside: 0,
    alerts: [],
    system_status: { ai: "running", database: "unknown" },
  });

  const [history, setHistory] = useState([]);
  const [page, setPage] = useState("live");
  const [historyData, setHistoryData] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStats(data);

      setHistory((prev) => {
        const updated = [...prev, data.current_inside];
        if (updated.length > 30) updated.shift();
        return updated;
      });
    };

    return () => ws.close();
  }, []);

  return (
    <div className="dashboard">
      {/* SIDEBAR */}
      <div className="sidebar">
        <h2>Retail AI</h2>
        <button onClick={() => setPage("live")}>Live Dashboard</button>
        <button
          onClick={() => {
            setPage("history");
            fetch("http://127.0.0.1:8000/history")
              .then((res) => res.json())
              .then((data) => setHistoryData(data));
          }}
        >
          Analytics
        </button>
      </div>

      {/* MAIN CONTENT */}
      <div className="main">
        {page === "live" && (
          <>
            <h1>Live Monitoring</h1>

            {/* STATUS */}
            <div className="status-row">
              <div className="status-card">
                AI:
                <span className={`badge ${stats.system_status?.ai}`}>
                  {stats.system_status?.ai}
                </span>
              </div>

              <div className="status-card">
                Database:
                <span className={`badge ${stats.system_status?.database}`}>
                  {stats.system_status?.database}
                </span>
              </div>
            </div>

            {/* CAMERA */}
            <div className="camera-card">
              <img
                src="http://127.0.0.1:8000/video"
                alt="Live Feed"
              />
            </div>

            {/* METRICS */}
            <div className="metrics-grid">
              <div className="metric-card">
                <h3>Current Inside</h3>
                <p>{stats.current_inside}</p>
              </div>

              <div className="metric-card">
                <h3>Total Entered</h3>
                <p>{stats.count_in}</p>
              </div>

              <div className="metric-card">
                <h3>Total Exited</h3>
                <p>{stats.count_out}</p>
              </div>
            </div>

            {/* ALERTS */}
            <div className="alerts-card">
              <h3>Alerts</h3>
              {stats.alerts.length > 0 ? (
                stats.alerts.map((alert, index) => (
                  <div key={index} className={`alert ${alert.type}`}>
                    {alert.message}
                  </div>
                ))
              ) : (
                <p>No alerts</p>
              )}
            </div>

            {/* GRAPH */}
            <div className="graph-card">
              <h3>Occupancy Trend</h3>
              <Line
                data={{
                  labels: history.map((_, i) => i + 1),
                  datasets: [
                    {
                      label: "Current Inside",
                      data: history,
                      borderColor: "#3b82f6",
                      fill: false,
                    },
                  ],
                }}
              />
            </div>
          </>
        )}

        {page === "history" && historyData && (
        <>
          <h1>Analytics Dashboard</h1>

          <div className="metrics-grid">
            <div className="metric-card">
              <h3>Total Customers</h3>
              <p>{historyData.total_customers}</p>
            </div>

            <div className="metric-card">
              <h3>Average Dwell (sec)</h3>
              <p>{historyData.avg_dwell}</p>
            </div>

            <div className="metric-card">
              <h3>Peak Traffic</h3>
              <p>{historyData.peak_traffic}</p>
            </div>
          </div>

          <div className="graph-row">

          <div className="graph-card">
            <h3>Entry Trend (Customers per Day)</h3>
            <Line
              data={{
                labels: historyData.trend_dates,
                datasets: [
                  {
                    label: "Entries",
                    data: historyData.trend_counts,
                    borderColor: "#3b82f6",
                    fill: false,
                  },
                ],
              }}
              options={{
                responsive: true,
                plugins: {
                  legend: { display: true },
                },
                scales: {
                  x: {
                    title: {
                      display: true,
                      text: "Date",
                    },
                  },
                  y: {
                    title: {
                      display: true,
                      text: "Number of Customers",
                    },
                    beginAtZero: true,
                  },
                },
              }}
            />
          </div>

          <div className="graph-card">
            <h3>Dwell Time Distribution</h3>
            <Line
              data={{
                labels: historyData.dwell_distribution.map((_, i) => i + 1),
                datasets: [
                  {
                    label: "Dwell Time (seconds)",
                    data: historyData.dwell_distribution,
                    borderColor: "#16a34a",
                    fill: false,
                  },
                ],
              }}
              options={{
                responsive: true,
                plugins: {
                  legend: { display: true },
                },
                scales: {
                  x: {
                    title: {
                      display: true,
                      text: "Customer Session Index",
                    },
                  },
                  y: {
                    title: {
                      display: true,
                      text: "Dwell Time (seconds)",
                    },
                    beginAtZero: true,
                  },
                },
              }}
            />
          </div>

        </div>

        </>
      )}

      </div>
    </div>
  );
}

export default App;
