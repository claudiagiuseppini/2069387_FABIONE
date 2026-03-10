export const chartState = {
  instance: null,
  selectedMetricKey: "",
  history: {}
};

export function initChart() {
  const canvas = document.getElementById("live-chart");

  if (!canvas) {
    console.error("Canvas live-chart non trovato");
    return;
  }

  if (chartState.instance) {
    chartState.instance.destroy();
  }

  chartState.instance = new Chart(canvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "No metric selected",
          data: [],
          borderWidth: 2,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: {
          ticks: {
            color: "#94a3b8"
          },
          grid: {
            color: "rgba(255,255,255,0.08)"
          }
        },
        y: {
          ticks: {
            color: "#94a3b8"
          },
          grid: {
            color: "rgba(255,255,255,0.08)"
          }
        }
      },
      plugins: {
        legend: {
          labels: {
            color: "#f1f5f9"
          }
        }
      }
    }
  });
}

export function updateChartForSelectedMetric() {
  if (!chartState.instance) return;

  if (!chartState.history || typeof chartState.history !== "object") {
    chartState.history = {};
  }

  const selectedKey = chartState.selectedMetricKey;
  const points = chartState.history[selectedKey] || [];

  chartState.instance.data.labels = points.map(point => point.x);
  chartState.instance.data.datasets[0].data = points.map(point => point.y);
  chartState.instance.data.datasets[0].label = selectedKey || "No metric selected";

  chartState.instance.update();
}

export function appendPointToChartHistory(metricKey, point, maxPoints = 20) {
  if (!chartState.history || typeof chartState.history !== "object") {
    chartState.history = {};
  }

  if (!chartState.history[metricKey]) {
    chartState.history[metricKey] = [];
  }

  chartState.history[metricKey].push(point);

  if (chartState.history[metricKey].length > maxPoints) {
    chartState.history[metricKey] = chartState.history[metricKey].slice(-maxPoints);
  }
}

export function addSensorToChartHistory(sensor) {
  if (!sensor) return;
  if (sensor.value === null || sensor.value === undefined) return;

  const numericValue = Number(sensor.value);
  if (Number.isNaN(numericValue)) return;

  const metricKey = `${sensor.sensor_id}|${sensor.metric_name}`;

  let label;
  if (sensor.timestamp) {
    const date = new Date(sensor.timestamp);
    label = Number.isNaN(date.getTime())
      ? String(sensor.timestamp)
      : date.toLocaleTimeString();
  } else {
    label = new Date().toLocaleTimeString();
  }

  appendPointToChartHistory(metricKey, {
    x: label,
    y: numericValue
  });
}