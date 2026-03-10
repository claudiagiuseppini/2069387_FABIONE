export const SENSOR_GROUPS = [
  {
    key: "priority",
    title: "PRIORITY",
    sensors: [
      "airlock",
      "greenhouse_temperature",
      "life_support",
      "radiation",
      "water_tank_level"
    ]
  },
  {
    key: "air",
    title: "AIR",
    sensors: [
      "co2_hall",
      "air_quality_pm25",
      "air_quality_voc"
    ]
  },
  {
    key: "power",
    title: "POWER",
    sensors: [
      "power_consumption",
      "power_bus",
      "solar_array"
    ]
  },
  {
    key: "miscellaneous",
    title: "MISCELLANEOUS",
    sensors: [
      "thermal_loop",
      "hydroponic_ph",
      "entrance_humidity",
      "corridor_pressure"
    ]
  }
];

export function groupSensorsByCategories(sensors) {
  const groups = new Map();

  SENSOR_GROUPS.forEach(group => {
    groups.set(group.key, {
      key: group.key,
      title: group.title,
      metrics: []
    });
  });

  sensors.forEach(sensor => {
    let found = false;

    for (const group of SENSOR_GROUPS) {
      if (group.sensors.includes(sensor.sensor_id)) {
        groups.get(group.key).metrics.push(sensor);
        found = true;
        break;
      }
    }

    if (!found && groups.has("miscellaneous")) {
      groups.get("miscellaneous").metrics.push(sensor);
    }
  });

  return SENSOR_GROUPS
    .map(group => groups.get(group.key))
    .filter(group => group.metrics.length > 0);
}

export function buildMetricRow(sensor, helpers) {
  const {
    safeText,
    formatRelativeTime,
    statusClass,
    doesSensorViolateRules
  } = helpers;

  const value = safeText(sensor.value);
  const unit = safeText(sensor.unit, "");
  const metricName = safeText(sensor.metric_name);
  const status = safeText(sensor.status, "ok");
  const source = safeText(sensor.source, sensor.sensor_id);
  const timestamp = formatRelativeTime(sensor.timestamp);
  const isAlert = doesSensorViolateRules(sensor);

  return `
    <div class="metric-row ${isAlert ? "metric-row-alert" : ""}">
      <div class="metric-row-main">
        <div class="metric-row-name">
          ${metricName}
          ${unit ? `<span class="metric-row-unit">${unit}</span>` : ""}
        </div>
        <div class="metric-row-value">${value}</div>
      </div>

      <div class="metric-row-meta">
        <span class="sensor-status ${statusClass(status)}">${status}</span>
        <span><strong>Source:</strong> ${source}</span>
        <span><strong>Updated:</strong> ${timestamp}</span>
        ${isAlert ? `<span class="metric-row-rule-alert">Rule violated</span>` : ""}
      </div>
    </div>
  `;
}

export function bindSensorGroupToggles({ container, appState }) {
  const toggles = container.querySelectorAll(".sensor-group-toggle");

  toggles.forEach(toggle => {
    toggle.addEventListener("click", () => {
      const groupName = toggle.dataset.sensorGroup;
      const details = toggle.nextElementSibling;

      if (!groupName || !details) return;

      const isOpen = appState.openGroups.has(groupName);

      if (isOpen) {
        appState.openGroups.delete(groupName);
        toggle.classList.add("collapsed");
        toggle.setAttribute("aria-expanded", "false");
        details.classList.remove("open");
      } else {
        appState.openGroups.add(groupName);
        toggle.classList.remove("collapsed");
        toggle.setAttribute("aria-expanded", "true");
        details.classList.add("open");
      }
    });
  });
}

export function populateChartSelect({
  sensors,
  chartSensorSelect,
  chartState
}) {
  const previousValue = chartSensorSelect.value || chartState.selectedMetricKey || "";

  const uniqueSensors = [];
  const seen = new Set();

  sensors.forEach(sensor => {
    const value = `${sensor.sensor_id}|${sensor.metric_name}`;
    if (seen.has(value)) return;
    seen.add(value);

    uniqueSensors.push({
      value,
      label: `${sensor.sensor_id} - ${sensor.metric_name}`
    });
  });

  const options = uniqueSensors.map(sensor => {
    return `<option value="${sensor.value}">${sensor.label}</option>`;
  });

  chartSensorSelect.innerHTML = `
    <option value="">Seleziona metrica</option>
    ${options.join("")}
  `;

  const valueStillExists = uniqueSensors.some(sensor => sensor.value === previousValue);

  if (valueStillExists) {
    chartSensorSelect.value = previousValue;
    chartState.selectedMetricKey = previousValue;
  } else {
    chartSensorSelect.value = "";
    chartState.selectedMetricKey = "";
  }
}

export function renderSensorCards({
  latestSensors,
  sensorCardsContainer,
  chartSensorSelect,
  appState,
  chartState,
  helpers
}) {
  const {
    sanitizeGroupKey,
    buildMetricRowHelpers
  } = helpers;

  if (!latestSensors.length) {
    sensorCardsContainer.innerHTML = `
      <div class="col-12">
        <div class="placeholder-box text-center text-secondary py-5 rounded border border-secondary-subtle">
          Nessun dato disponibile
        </div>
      </div>
    `;

    populateChartSelect({
      sensors: [],
      chartSensorSelect,
      chartState
    });

    return;
  }

  const scrollPositions = {};
  document.querySelectorAll(".sensor-group-details.open").forEach(el => {
    scrollPositions[el.id] = el.scrollTop;
  });

  sensorCardsContainer.classList.add("no-transition");

  const groupedSensors = groupSensorsByCategories(latestSensors);

  const html = groupedSensors.map(group => {
    const groupKey = sanitizeGroupKey(group.key);
    const collapseId = `sensor-group-${groupKey}`;
    const isOpen = appState.openGroups.has(group.key);
    const sensorsCount = new Set(group.metrics.map(s => s.sensor_id)).size;
    const metricsCount = group.metrics.length;

    const sensorGroups = group.metrics.reduce((acc, sensor) => {
      const id = sensor.sensor_id;
      if (!acc[id]) acc[id] = [];
      acc[id].push(sensor);
      return acc;
    }, {});

    return `
      <div class="col-12">
        <div class="sensor-card sensor-group-card">
          <button
            class="sensor-group-toggle ${isOpen ? "" : "collapsed"}"
            type="button"
            data-sensor-group="${group.key}"
            aria-expanded="${isOpen ? "true" : "false"}"
            aria-controls="${collapseId}"
          >
            <div class="sensor-group-header">
              <div>
                <div class="sensor-title mb-1">${group.title}</div>
                <div class="sensor-subtitle mb-0">
                  ${sensorsCount} sensor${sensorsCount !== 1 ? "s" : ""} · ${metricsCount} metric${metricsCount !== 1 ? "s" : ""}
                </div>
              </div>

              <div class="sensor-group-chevron">
                <i class="bi bi-chevron-down"></i>
              </div>
            </div>
          </button>

          <div id="${collapseId}" class="sensor-group-details ${isOpen ? "open" : ""}">
            <div class="category-sensors">
              ${Object.entries(sensorGroups).map(([sensorId, sensors]) => `
                <div class="sensor-section">
                  <h6 class="sensor-section-title">${sensorId}</h6>
                  <div class="sensor-group-metrics">
                    ${sensors.map(sensor => buildMetricRow(sensor, buildMetricRowHelpers)).join("")}
                  </div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join("");

  sensorCardsContainer.innerHTML = html;

  Object.entries(scrollPositions).forEach(([id, top]) => {
    const el = document.getElementById(id);
    if (el) el.scrollTop = top;
  });

  sensorCardsContainer.classList.remove("no-transition");

  bindSensorGroupToggles({
    container: sensorCardsContainer,
    appState
  });

  populateChartSelect({
    sensors: latestSensors,
    chartSensorSelect,
    chartState
  });
}