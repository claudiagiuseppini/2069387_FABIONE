/* =========================
   CONFIG
========================= */

const API_BASE = "http://localhost:8000";

const API_CONFIG = {
  latestState: `${API_BASE}/api/latest`,
  rules: `${API_BASE}/api/rules`,
  resetRules: `${API_BASE}/api/rules/reset`,
  actuators: `${API_BASE}/api/actuators`,
  events: `${API_BASE}/api/events`,
  health: `${API_BASE}/api/health`,
  dashboardStream: `${API_BASE}/api/stream/dashboard`
};

const STREAM_CONFIG = {
  fallbackPollingMs: 10000
};

/* =========================
   STATE
========================= */

const appState = {
  latestSensors: [],
  rules: [],
  editingRuleId: null,
  actuators: {
    cooling_fan: "OFF",
    entrance_humidifier: "OFF",
    hall_ventilation: "OFF",
    habitat_heater: "OFF"
  },
  eventLog: [],
  openSensorGroups: new Set()
};

const streamState = {
  source: null,
  fallbackTimer: null,
  connected: false
};

/* =========================
   DOM REFERENCES
========================= */

const dom = {
  activeSensorsCount: document.getElementById("active-sensors-count"),
  liveTelemetryCount: document.getElementById("live-telemetry-count"),
  activeRulesCount: document.getElementById("active-rules-count"),
  activeActuatorsCount: document.getElementById("active-actuators-count"),
  lastUpdateLabel: document.getElementById("last-update-label"),
  systemStatusBadge: document.getElementById("system-status-badge"),

  sensorCardsContainer: document.getElementById("sensor-cards-container"),
  sensorCardsBadge: document.getElementById("sensor-cards-badge"),

  rulesTableBody: document.getElementById("rules-table-body"),
  eventLogList: document.getElementById("event-log-list"),
  chartSensorSelect: document.getElementById("chart-sensor-select"),

  refreshButton: document.getElementById("refresh-dashboard-btn"),
  resetRulesButton: document.getElementById("reset-rules-btn"),
  toastContainer: document.getElementById("toast-container"),

  ruleForm: document.getElementById("rule-form"),
  sensorNameInput: document.getElementById("sensor-name"),
  metricNameInput: document.getElementById("metric-name"),
  ruleOperatorInput: document.getElementById("rule-operator"),
  ruleThresholdInput: document.getElementById("rule-threshold"),
  actuatorNameInput: document.getElementById("actuator-name"),
  actionValueInput: document.getElementById("action-value"),
  ruleEnabledInput: document.getElementById("rule-enabled")
};

const ruleModalElements = {
  modal: document.getElementById("ruleModal"),
  title: document.getElementById("ruleModalLabel"),
  submitButton: document.getElementById("rule-submit-btn")
};

/* =========================
   HELPERS
========================= */

function nowLabel() {
  return new Date().toLocaleTimeString("it-IT");
}

function safeText(value, fallback = "--") {
  return value === null || value === undefined || value === "" ? fallback : value;
}

function parseTimestamp(timestamp) {
  if (timestamp === null || timestamp === undefined || timestamp === "") {
    return null;
  }

  if (typeof timestamp === "number") {
    const ms = timestamp < 1e12 ? timestamp * 1000 : timestamp;
    const date = new Date(ms);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  const str = String(timestamp).trim();

  if (/^\d+$/.test(str)) {
    const numeric = Number(str);
    const ms = numeric < 1e12 ? numeric * 1000 : numeric;
    const date = new Date(ms);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  const normalized = str.replace(/\.(\d{3})\d+/, ".$1");
  const date = new Date(normalized);

  return Number.isNaN(date.getTime()) ? null : date;
}

function formatRelativeTime(timestamp) {
  const date = parseTimestamp(timestamp);
  if (!date) return "--";

  let diffSeconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (diffSeconds < 0) diffSeconds = 0;

  const hours = Math.floor(diffSeconds / 3600);
  const minutes = Math.floor((diffSeconds % 3600) / 60);
  const seconds = diffSeconds % 60;

  const mm = String(minutes).padStart(2, "0");
  const ss = String(seconds).padStart(2, "0");

  if (hours > 0) {
    const hh = String(hours).padStart(2, "0");
    return `${hh}:${mm}:${ss} ago`;
  }

  return `${mm}:${ss} ago`;
}

function normalizeOperator(operator) {
  if (operator === "=") return "==";
  return operator;
}

function evaluateRule(value, operator, threshold) {
  const numericValue = Number(value);
  const numericThreshold = Number(threshold);

  if (Number.isNaN(numericValue) || Number.isNaN(numericThreshold)) {
    return false;
  }

  switch (normalizeOperator(operator)) {
    case ">":
      return numericValue > numericThreshold;
    case "<":
      return numericValue < numericThreshold;
    case ">=":
      return numericValue >= numericThreshold;
    case "<=":
      return numericValue <= numericThreshold;
    case "==":
      return numericValue === numericThreshold;
    default:
      return false;
  }
}

function isRuleEnabled(rule) {
  return rule.enabled === true || rule.enabled === 1;
}

function doesSensorViolateRules(sensor) {
  return appState.rules.some(rule => {
    if (!isRuleEnabled(rule)) return false;

    const sameSensor =
      String(rule.sensor_name || "").trim() === String(sensor.sensor_id || "").trim();

    const sameMetric =
      String(rule.metric_name || "").trim() === String(sensor.metric_name || "").trim();

    if (!sameSensor || !sameMetric) return false;

    return evaluateRule(sensor.value, rule.operator, rule.threshold);
  });
}

function statusClass(status) {
  const normalized = String(status || "").toLowerCase();

  if (normalized.includes("ok") || normalized.includes("on")) return "status-ok";
  if (normalized.includes("warn")) return "status-warning";
  if (normalized.includes("error") || normalized.includes("fail") || normalized.includes("off")) return "status-error";

  return "status-unknown";
}

function logEvent(message, type = "info") {
  const item = {
    id: Date.now() + Math.random(),
    message,
    type,
    time: nowLabel()
  };

  appState.eventLog.unshift(item);
  appState.eventLog = appState.eventLog.slice(0, 20);
  renderEventLog();
}

function showToast(title, message, type = "info") {
  const toastId = `toast-${Date.now()}`;

  let borderClass = "border-info";
  if (type === "success") borderClass = "border-success";
  if (type === "warning") borderClass = "border-warning";
  if (type === "danger" || type === "error") borderClass = "border-danger";

  const toastHtml = `
    <div id="${toastId}" class="toast ${borderClass}" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header">
        <strong class="me-auto">${title}</strong>
        <small class="text-secondary">${nowLabel()}</small>
        <button type="button" class="btn-close btn-close-white ms-2 mb-1" data-bs-dismiss="toast" aria-label="Chiudi"></button>
      </div>
      <div class="toast-body">
        ${message}
      </div>
    </div>
  `;

  dom.toastContainer.insertAdjacentHTML("beforeend", toastHtml);

  const toastElement = document.getElementById(toastId);
  const toast = new bootstrap.Toast(toastElement, { delay: 4000 });
  toast.show();

  toastElement.addEventListener("hidden.bs.toast", () => {
    toastElement.remove();
  });
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text}`);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

function groupSensorsBySource(sensors) {
  const groups = new Map();

  sensors.forEach(sensor => {
    const key = safeText(sensor.sensor_id, "unknown_sensor");

    if (!groups.has(key)) {
      groups.set(key, {
        sensorId: key,
        sensorType: safeText(sensor.sensor_type, "unknown"),
        metrics: []
      });
    }

    groups.get(key).metrics.push(sensor);
  });

  return Array.from(groups.values()).sort((a, b) =>
    a.sensorId.localeCompare(b.sensorId)
  );
}

function sanitizeGroupKey(value) {
  return String(value).replace(/[^a-zA-Z0-9_-]/g, "_");
}

function buildMetricRow(sensor) {
  const value = safeText(sensor.value);
  const unit = safeText(sensor.unit, "");
  const metricName = safeText(sensor.metric_name);
  const status = safeText(sensor.status, "unknown");
  const source = safeText(sensor.source, "n/a");
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

function bindSensorGroupToggles() {
  const toggles = dom.sensorCardsContainer.querySelectorAll(".sensor-group-toggle");

  toggles.forEach(toggle => {
    toggle.addEventListener("click", () => {
      const groupName = toggle.dataset.sensorGroup;
      const details = toggle.nextElementSibling;

      if (!groupName || !details) return;

      const isOpen = appState.openSensorGroups.has(groupName);

      if (isOpen) {
        appState.openSensorGroups.delete(groupName);
        toggle.classList.add("collapsed");
        toggle.setAttribute("aria-expanded", "false");
        details.classList.remove("open");
      } else {
        appState.openSensorGroups.add(groupName);
        toggle.classList.remove("collapsed");
        toggle.setAttribute("aria-expanded", "true");
        details.classList.add("open");
      }
    });
  });
}

/* =========================
   RENDER - OVERVIEW
========================= */

function updateOverview() {
  const uniqueSensorIds = new Set(appState.latestSensors.map(s => s.sensor_id));
  dom.activeSensorsCount.textContent = uniqueSensorIds.size;

  dom.sensorCardsBadge.textContent = `${uniqueSensorIds.size} categories · ${appState.latestSensors.length} metrics`;

  const telemetryCount = appState.latestSensors.filter(
    item => String(item.sensor_type || "").toLowerCase().includes("tele")
  ).length;
  dom.liveTelemetryCount.textContent = telemetryCount;

  const enabledRules = appState.rules.filter(isRuleEnabled).length;
  dom.activeRulesCount.textContent = enabledRules;

  const actuatorsOn = Object.values(appState.actuators).filter(
    state => String(state).toUpperCase() === "ON"
  ).length;
  dom.activeActuatorsCount.textContent = actuatorsOn;

  dom.lastUpdateLabel.textContent = `Time: ${nowLabel()}`;
}

/* =========================
   RENDER - SENSOR CARDS
========================= */

function renderSensorCards() {
  if (!appState.latestSensors.length) {
    dom.sensorCardsContainer.innerHTML = `
      <div class="col-12">
        <div class="placeholder-box text-center text-secondary py-5 rounded border border-secondary-subtle">
          Nessun dato disponibile
        </div>
      </div>
    `;
    populateChartSelect([]);
    return;
  }

  const groupedSensors = groupSensorsBySource(appState.latestSensors);

  const html = groupedSensors.map(group => {
    const groupKey = sanitizeGroupKey(group.sensorId);
    const collapseId = `sensor-group-${groupKey}`;
    const isOpen = appState.openSensorGroups.has(group.sensorId);
    const metricsCount = group.metrics.length;

    return `
      <div class="col-12">
        <div class="sensor-card sensor-group-card">
          <button
            class="sensor-group-toggle ${isOpen ? "" : "collapsed"}"
            type="button"
            data-sensor-group="${group.sensorId}"
            aria-expanded="${isOpen ? "true" : "false"}"
            aria-controls="${collapseId}"
          >
            <div class="sensor-group-header">
              <div>
                <div class="sensor-title mb-1">${group.sensorId}</div>
                <div class="sensor-subtitle mb-0">
                  ${group.sensorType} · ${metricsCount} metric${metricsCount !== 1 ? "s" : ""}
                </div>
              </div>

              <div class="sensor-group-chevron">
                <i class="bi bi-chevron-down"></i>
              </div>
            </div>
          </button>

          <div id="${collapseId}" class="sensor-group-details ${isOpen ? "open" : ""}">
            <div class="sensor-group-metrics">
              ${group.metrics.map(buildMetricRow).join("")}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join("");

  dom.sensorCardsContainer.innerHTML = html;
  bindSensorGroupToggles();
  populateChartSelect(appState.latestSensors);
}

function populateChartSelect(sensors) {
  const options = sensors.map(sensor => {
    const value = `${sensor.sensor_id}|${sensor.metric_name}`;
    const label = `${sensor.sensor_id} - ${sensor.metric_name}`;
    return `<option value="${value}">${label}</option>`;
  });

  dom.chartSensorSelect.innerHTML = `
    <option value="">Seleziona metrica</option>
    ${options.join("")}
  `;
}

/* =========================
   RENDER - RULES TABLE
========================= */

function renderRulesTable() {
  if (!appState.rules.length) {
    dom.rulesTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-secondary py-4">
          Nessuna regola caricata
        </td>
      </tr>
    `;
    return;
  }

  const html = appState.rules.map(rule => {
    const enabled = isRuleEnabled(rule);

    return `
      <tr>
        <td>${safeText(rule.sensor_name)}</td>
        <td>${safeText(rule.metric_name)}</td>
        <td>
          <span class="fw-semibold">${safeText(rule.operator)}</span>
          ${safeText(rule.threshold)}
        </td>
        <td>${safeText(rule.actuator_name)}</td>
        <td>${safeText(rule.action_value)}</td>
        <td>
          <span class="${enabled ? "rule-badge-enabled" : "rule-badge-disabled"}">
            ${enabled ? "Enabled" : "Disabled"}
          </span>
        </td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-info me-1 edit-rule-btn" data-id="${rule.id}">
            Edit
          </button>
          <button class="btn btn-sm btn-outline-light me-1 toggle-rule-btn" data-id="${rule.id}" data-enabled="${enabled}">
            ${enabled ? "Disable" : "Enable"}
          </button>
          <button class="btn btn-sm btn-outline-danger delete-rule-btn" data-id="${rule.id}">
            Delete
          </button>
        </td>
      </tr>
    `;
  }).join("");

  dom.rulesTableBody.innerHTML = html;
}

/* =========================
   RENDER - EVENT LOG
========================= */

function renderEventLog() {
  if (!appState.eventLog.length) {
    dom.eventLogList.innerHTML = `
      <li class="list-group-item bg-black text-secondary border-secondary">
        Nessun evento disponibile
      </li>
    `;
    return;
  }

  const html = appState.eventLog.map(event => `
    <li class="list-group-item border-secondary">
      <div class="text-white event-item event-${event.type}">
        <div class="text-white fw-semibold">${event.message}</div>
        <div class="text-white event-time">${event.time}</div>
      </div>
    </li>
  `).join("");

  dom.eventLogList.innerHTML = html;
}

/* =========================
   RENDER - ACTUATORS
========================= */

function renderActuators() {
  const actuatorItems = document.querySelectorAll(".actuator-item");

  actuatorItems.forEach(item => {
    const toggleButton = item.querySelector(".actuator-toggle-btn");
    if (!toggleButton) return;

    const actuatorId = toggleButton.dataset.actuator;
    const state = (appState.actuators[actuatorId] || "OFF").toUpperCase();

    toggleButton.textContent = state;
    toggleButton.classList.remove("actuator-on", "actuator-off");
    toggleButton.classList.add(state === "ON" ? "actuator-on" : "actuator-off");
  });
}

/* =========================
   FETCH DATA
========================= */

async function loadLatestState() {
  try {
    const data = await apiFetch(API_CONFIG.latestState);

    if (Array.isArray(data)) {
      appState.latestSensors = data;
    } else if (Array.isArray(data.items)) {
      appState.latestSensors = data.items;
    } else if (Array.isArray(data.latest)) {
      appState.latestSensors = data.latest;
    } else if (Array.isArray(data.data)) {
      appState.latestSensors = data.data;
    } else {
      appState.latestSensors = [];
    }

    renderSensorCards();
    updateOverview();

    logEvent("Sensor state updated", "info");
  } catch (error) {
    console.error("Errore loadLatestState:", error);
    showToast("Errore", "Impossible to load sensor states", "danger");
    logEvent("Error loading sensors", "danger");
  }
}

async function loadRules() {
  try {
    const data = await apiFetch(API_CONFIG.rules);

    if (Array.isArray(data)) {
      appState.rules = data;
    } else if (Array.isArray(data.rules)) {
      appState.rules = data.rules;
    } else if (Array.isArray(data.items)) {
      appState.rules = data.items;
    } else {
      appState.rules = [];
    }

    renderRulesTable();
    renderSensorCards();
    updateOverview();

    logEvent("Rules Updated", "info");
  } catch (error) {
    console.error("Errore loadRules:", error);
    showToast("Errore", "Impossible to load the rules", "danger");
    logEvent("Error loading rules", "danger");
  }
}

async function loadHealth() {
  try {
    const data = await apiFetch(API_CONFIG.health);
    updateSystemBadge(data);
  } catch (error) {
    dom.systemStatusBadge.textContent = "System Offline";
    dom.systemStatusBadge.className = "badge rounded-pill text-bg-danger";
  }
}

async function loadActuators() {
  try {
    const data = await apiFetch(API_CONFIG.actuators);

    if (data && typeof data === "object" && !Array.isArray(data)) {
      appState.actuators = {
        ...appState.actuators,
        ...Object.fromEntries(
          Object.entries(data).map(([key, value]) => [
            key,
            String(value || "OFF").toUpperCase()
          ])
        )
      };
    }

    renderActuators();
    updateOverview();
  } catch (error) {
    console.error("Errore loadActuators:", error);
    logEvent("Errore caricamento attuatori", "danger");
  }
}

function updateSystemBadge(data) {
  const ok = data?.status || data?.ok || data?.service;
  dom.systemStatusBadge.textContent = ok ? "System Online" : "System Degraded";
  dom.systemStatusBadge.className = ok
    ? "badge rounded-pill text-bg-success"
    : "badge rounded-pill text-bg-danger";
}

function applyDashboardSnapshot(snapshot) {
  if (Array.isArray(snapshot.latest)) {
    appState.latestSensors = snapshot.latest;
    renderSensorCards();
  }

  if (snapshot.actuators && typeof snapshot.actuators === "object") {
    appState.actuators = {
      ...appState.actuators,
      ...Object.fromEntries(
        Object.entries(snapshot.actuators).map(([key, value]) => [
          key,
          String(value || "OFF").toUpperCase()
        ])
      )
    };
    renderActuators();
  }

  if (snapshot.health && typeof snapshot.health === "object") {
    updateSystemBadge(snapshot.health);
  }

  updateOverview();
}

/* =========================
   STREAM
========================= */

function stopFallbackPolling() {
  if (streamState.fallbackTimer) {
    clearInterval(streamState.fallbackTimer);
    streamState.fallbackTimer = null;
  }
}

function startFallbackPolling() {
  if (streamState.fallbackTimer) return;

  streamState.fallbackTimer = setInterval(async () => {
    await loadHealth();
    await loadLatestState();
    await loadActuators();
  }, STREAM_CONFIG.fallbackPollingMs);
}

function closeDashboardStream() {
  if (streamState.source) {
    streamState.source.close();
    streamState.source = null;
  }

  streamState.connected = false;
}

function startDashboardStream() {
  if (typeof EventSource === "undefined") {
    startFallbackPolling();
    return;
  }

  closeDashboardStream();

  const source = new EventSource(API_CONFIG.dashboardStream);
  streamState.source = source;

  source.onopen = () => {
    const firstConnect = !streamState.connected;
    streamState.connected = true;
    stopFallbackPolling();

    if (firstConnect) {
      logEvent("SSE connesso: aggiornamenti real-time attivi", "success");
    }
  };

  source.onmessage = event => {
    try {
      const snapshot = JSON.parse(event.data);
      applyDashboardSnapshot(snapshot);
    } catch (error) {
      console.error("Errore parsing evento SSE:", error);
    }
  };

  source.onerror = () => {
    if (streamState.connected) {
      logEvent("SSE disconnesso: attivo fallback polling", "warning");
      streamState.connected = false;
    }

    startFallbackPolling();
  };
}

/* =========================
   ACTUATOR ACTIONS
========================= */

async function sendActuatorCommand(actuatorId, state) {
  try {
    await apiFetch(`${API_CONFIG.actuators}/${actuatorId}`, {
      method: "POST",
      body: JSON.stringify({ state })
    });

    appState.actuators[actuatorId] = state;
    renderActuators();
    updateOverview();

    showToast("Actuator", `${actuatorId} set on ${state}`, "success");
    logEvent(`Actuator Command: ${actuatorId} -> ${state}`, "success");
  } catch (error) {
    console.error("Errore sendActuatorCommand:", error);
    showToast("Errore", `Impossible to load ${actuatorId}`, "danger");
    logEvent(`Error command actuator ${actuatorId}`, "danger");
  }
}

/* =========================
   RULE ACTIONS
========================= */

async function createRule(payload) {
  try {
    await apiFetch(API_CONFIG.rules, {
      method: "POST",
      body: JSON.stringify(payload)
    });

    showToast("New Rule", "New rule saved correctly", "success");
    logEvent(`New rule created on ${payload.sensor_name}.${payload.metric_name}`, "success");

    await loadRules();
    return true;
  } catch (error) {
    console.error("Errore createRule:", error);
    showToast("Errore", "Impossible to create rule", "danger");
    logEvent("Error in creating rule", "danger");
    return false;
  }
}

async function updateRule(ruleId, payload) {
  try {
    await apiFetch(`${API_CONFIG.rules}/${ruleId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });

    showToast("Rule updated", `Rule ${ruleId} updated correctly`, "success");
    logEvent(`Rule ${ruleId} edited`, "warning");

    await loadRules();
    return true;
  } catch (error) {
    console.error("Errore updateRule:", error);
    showToast("Errore", `Impossible to update rule ${ruleId}`, "danger");
    logEvent(`Error updating rule ${ruleId}`, "danger");
    return false;
  }
}

async function toggleRule(ruleId, enabled) {
  try {
    await apiFetch(`${API_CONFIG.rules}/${ruleId}`, {
      method: "PUT",
      body: JSON.stringify({ enabled: !enabled })
    });

    showToast("Rule updated", `Rule ${ruleId} updated`, "success");
    logEvent(`Rule ${ruleId} ${enabled ? "disabled" : "enabled"}`, "warning");

    await loadRules();
  } catch (error) {
    console.error("Errore toggleRule:", error);
    showToast("Errore", `Impossible to update rule ${ruleId}`, "danger");
    logEvent(`Error update rule ${ruleId}`, "danger");
  }
}

async function deleteRule(ruleId) {
  try {
    await apiFetch(`${API_CONFIG.rules}/${ruleId}`, {
      method: "DELETE"
    });

    showToast("Rule deleted", `Rule ${ruleId} deleted`, "warning");
    logEvent(`Rule ${ruleId} deleted`, "warning");

    await loadRules();
  } catch (error) {
    console.error("Error deleteRule:", error);
    showToast("Error", `Impossible to delete rule ${ruleId}`, "danger");
    logEvent(`Error deleting rule ${ruleId}`, "danger");
  }
}

async function resetRulesToDefault() {
  try {
    const response = await apiFetch(API_CONFIG.resetRules, {
      method: "POST"
    });

    const resetCount = Number(response?.reset_count || 0);

    showToast("Rules reset", `Ripristinate ${resetCount} regole di default`, "warning");
    logEvent(`Regole ripristinate ai default (${resetCount})`, "warning");

    await loadRules();
    return true;
  } catch (error) {
    console.error("Errore resetRulesToDefault:", error);
    showToast("Errore", "Impossible to reset default rules", "danger");
    logEvent("Error resetting rules", "danger");
    return false;
  }
}

/* =========================
   FORM HANDLING
========================= */

function getRuleFormPayload() {
  return {
    sensor_name: dom.sensorNameInput.value.trim(),
    metric_name: dom.metricNameInput.value.trim(),
    operator: dom.ruleOperatorInput.value,
    threshold: parseFloat(dom.ruleThresholdInput.value),
    actuator_name: dom.actuatorNameInput.value,
    action_value: dom.actionValueInput.value,
    enabled: dom.ruleEnabledInput.checked
  };
}

function setRuleFormModeEditing(rule) {
  appState.editingRuleId = rule.id;

  dom.sensorNameInput.value = safeText(rule.sensor_name, "");
  dom.metricNameInput.value = safeText(rule.metric_name, "");
  dom.ruleOperatorInput.value = rule.operator === "==" ? "=" : safeText(rule.operator, ">");
  dom.ruleThresholdInput.value = safeText(rule.threshold, "");
  dom.actuatorNameInput.value = safeText(rule.actuator_name, "cooling_fan");
  dom.actionValueInput.value = safeText(rule.action_value, "OFF");
  dom.ruleEnabledInput.checked = isRuleEnabled(rule);

  ruleModalElements.title.textContent = `Edit Automation Rule #${rule.id}`;
  ruleModalElements.submitButton.textContent = "Update Rule";
}

function openEditRuleModal(ruleId) {
  const rule = appState.rules.find(item => String(item.id) === String(ruleId));
  if (!rule) {
    showToast("Errore", `Rule ${ruleId} not found`, "danger");
    return;
  }

  setRuleFormModeEditing(rule);
  const modal = bootstrap.Modal.getOrCreateInstance(ruleModalElements.modal);
  modal.show();
}

function setRuleFormModeCreate() {
  appState.editingRuleId = null;
  ruleModalElements.title.textContent = "Create Automation Rule";
  ruleModalElements.submitButton.textContent = "Save Rule";
}

function resetRuleForm() {
  dom.ruleForm.reset();
  dom.ruleEnabledInput.checked = true;
  setRuleFormModeCreate();
}

async function handleRuleSubmit(event) {
  event.preventDefault();

  const payload = getRuleFormPayload();

  if (!payload.sensor_name || !payload.metric_name || Number.isNaN(payload.threshold)) {
    showToast("Form not valid", "Fill all mandatory entries", "warning");
    return;
  }

  const submitOk = appState.editingRuleId === null
    ? await createRule(payload)
    : await updateRule(appState.editingRuleId, payload);

  if (!submitOk) {
    return;
  }

  const modalInstance = bootstrap.Modal.getInstance(ruleModalElements.modal);
  if (modalInstance) {
    modalInstance.hide();
  }

  resetRuleForm();
}

/* =========================
   EVENTS BINDING
========================= */

function bindStaticEvents() {
  dom.refreshButton.addEventListener("click", async () => {
    await refreshDashboard();
    showToast("Refresh", "Dashboard refreshed", "info");
  });

  if (dom.resetRulesButton) {
    dom.resetRulesButton.addEventListener("click", async () => {
      const confirmed = confirm("Ripristinare tutte le regole ai valori di default? Questa azione sovrascrive modifiche, aggiunte e cancellazioni.");
      if (!confirmed) return;
      await resetRulesToDefault();
    });
  }

  dom.ruleForm.addEventListener("submit", handleRuleSubmit);

  ruleModalElements.modal.addEventListener("hidden.bs.modal", () => {
    resetRuleForm();
  });

  ruleModalElements.modal.addEventListener("show.bs.modal", event => {
    const opener = event.relatedTarget;
    if (opener && opener.hasAttribute("data-create-rule")) {
      resetRuleForm();
    }
  });

 document.querySelectorAll(".actuator-toggle-btn").forEach(button => {
  button.addEventListener("click", () => {
    const actuatorId = button.dataset.actuator;
    const currentState = (appState.actuators[actuatorId] || "OFF").toUpperCase();
    const newState = currentState === "ON" ? "OFF" : "ON";

      sendActuatorCommand(actuatorId, newState);
    });
  });

  document.addEventListener("click", async event => {
    const editBtn = event.target.closest(".edit-rule-btn");
    if (editBtn) {
      openEditRuleModal(editBtn.dataset.id);
      return;
    }

    const toggleBtn = event.target.closest(".toggle-rule-btn");
    if (toggleBtn) {
      const ruleId = toggleBtn.dataset.id;
      const enabled = toggleBtn.dataset.enabled === "true";
      await toggleRule(ruleId, enabled);
      return;
    }

    const deleteBtn = event.target.closest(".delete-rule-btn");
    if (deleteBtn) {
      const ruleId = deleteBtn.dataset.id;
      const confirmed = confirm(`Deleting rule ${ruleId}?`);
      if (confirmed) {
        await deleteRule(ruleId);
      }
    }
  });
}

/* =========================
   REFRESH
========================= */

async function refreshDashboard() {
  await Promise.all([
    loadHealth(),
    loadLatestState(),
    loadRules(),
    loadActuators()
  ]);

  renderActuators();
  updateOverview();
}

/* =========================
   INIT
========================= */

async function init() {
  bindStaticEvents();

  logEvent("Initialized frontend", "info");

  await refreshDashboard();
  startDashboardStream();
}

document.addEventListener("DOMContentLoaded", init);