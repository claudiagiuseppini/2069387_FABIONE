/* =========================
   CONFIG
========================= */

const API_BASE = "http://localhost:8000";

const API_CONFIG = {
  latestState: `${API_BASE}/api/latest`,
  rules: `${API_BASE}/api/rules`,
  actuators: `${API_BASE}/api/actuators`,
  events: `${API_BASE}/api/events`,
  health: `${API_BASE}/api/health`
};

/* =========================
   STATE
========================= */

const appState = {
  latestSensors: [],
  rules: [],
  actuators: {
    cooling_fan: "OFF",
    entrance_humidifier: "OFF",
    hall_ventilation: "OFF",
    habitat_heater: "OFF"
  },
  eventLog: []
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
  toastContainer: document.getElementById("toast-container"),

  ruleForm: document.getElementById("rule-form"),
  sensorNameInput: document.getElementById("sensor-name"),
  metricNameInput: document.getElementById("metric-name"),
  ruleOperatorInput: document.getElementById("rule-operator"),
  ruleThresholdInput: document.getElementById("rule-threshold"),
  ruleUnitInput: document.getElementById("rule-unit"),
  actuatorNameInput: document.getElementById("actuator-name"),
  actionValueInput: document.getElementById("action-value"),
  ruleEnabledInput: document.getElementById("rule-enabled")
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

function statusClass(status) {
  const normalized = String(status || "").toLowerCase();

  if (normalized.includes("ok") || normalized.includes("on")) return "status-ok";
  if (normalized.includes("warn")) return "status-warning";
  if (normalized.includes("error") || normalized.includes("fail") || normalized.includes("off")) return "status-error";
  return "status-unknown";
}

function actuatorBadgeClass(state) {
  const normalized = String(state || "").toUpperCase();
  if (normalized === "ON") return "text-bg-success";
  if (normalized === "OFF") return "text-bg-danger";
  return "text-bg-secondary";
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

/* =========================
   RENDER - OVERVIEW
========================= */

function updateOverview() {

  const uniqueSensorIds = new Set(appState.latestSensors.map(s => s.sensor_id));
  dom.activeSensorsCount.textContent = uniqueSensorIds.size;

  dom.sensorCardsBadge.textContent = `${appState.latestSensors.length} metrics`;
  
  const telemetryCount = appState.latestSensors.filter(
    item => String(item.sensor_type || "").toLowerCase().includes("tele")
  ).length;
  dom.liveTelemetryCount.textContent = telemetryCount;

  const enabledRules = appState.rules.filter(
    rule => rule.enabled === true || rule.enabled === 1
  ).length;
  dom.activeRulesCount.textContent = enabledRules;

  const actuatorsOn = Object.values(appState.actuators).filter(
    state => String(state).toUpperCase() === "ON"
  ).length;
  dom.activeActuatorsCount.textContent = actuatorsOn;

  dom.lastUpdateLabel.textContent = `Last update: ${nowLabel()}`;
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

  const html = appState.latestSensors.map(sensor => {
    const value = safeText(sensor.value);
    const unit = safeText(sensor.unit, "");
    const metricName = safeText(sensor.metric_name);
    const status = safeText(sensor.status, "unknown");
    const source = safeText(sensor.source, "n/a");
    const timestamp = safeText(sensor.timestamp, "--");

    return `
      <div class="col-12 col-md-6 col-xl-4">
        <div class="sensor-card">
          <div class="sensor-title">${safeText(sensor.sensor_id)}</div>
          <div class="sensor-subtitle">
            ${metricName} · ${safeText(sensor.sensor_type)}
          </div>

          <div class="d-flex align-items-end gap-1 mb-2">
            <span class="sensor-value">${value}</span>
            <span class="sensor-unit">${unit}</span>
          </div>

          <span class="sensor-status ${statusClass(status)}">
            ${status}
          </span>

          <div class="sensor-meta">
            <div><strong>Source:</strong> ${source}</div>
            <div><strong>Timestamp:</strong> ${timestamp}</div>
          </div>
        </div>
      </div>
    `;
  }).join("");

  dom.sensorCardsContainer.innerHTML = html;
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
        <td colspan="8" class="text-center text-secondary py-4">
          Nessuna regola caricata
        </td>
      </tr>
    `;
    return;
  }

  const html = appState.rules.map(rule => {
    const enabled = rule.enabled === true || rule.enabled === 1;
    return `
      <tr>
        <td>${safeText(rule.id)}</td>
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
      <div class="event-item event-${event.type}">
        <div class="fw-semibold">${event.message}</div>
        <div class="event-time">${event.time}</div>
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

    // Supporta due casi:
    // 1. array diretto
    // 2. oggetto con proprietà items/latest/data
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

    logEvent("Stato sensori aggiornato", "info");
  } catch (error) {
    console.error("Errore loadLatestState:", error);
    showToast("Errore", "Impossibile caricare lo stato sensori", "danger");
    logEvent("Errore caricamento sensori", "danger");
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
    updateOverview();

    logEvent("Regole aggiornate", "info");
  } catch (error) {
    console.error("Errore loadRules:", error);
    showToast("Errore", "Impossibile caricare le regole", "danger");
    logEvent("Errore caricamento regole", "danger");
  }
}

async function loadHealth() {
  try {
    const data = await apiFetch(API_CONFIG.health);

    const ok = data.status || data.ok || data.service;
    dom.systemStatusBadge.textContent = ok ? "System Online" : "System Degraded";
    dom.systemStatusBadge.className = ok
      ? "badge rounded-pill text-bg-success"
      : "badge rounded-pill text-bg-danger";
  } catch (error) {
    dom.systemStatusBadge.textContent = "System Offline";
    dom.systemStatusBadge.className = "badge rounded-pill text-bg-danger";
  }
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

    showToast("Attuatore", `${actuatorId} impostato su ${state}`, "success");
    logEvent(`Comando attuatore: ${actuatorId} -> ${state}`, "success");
  } catch (error) {
    console.error("Errore sendActuatorCommand:", error);
    showToast("Errore", `Impossibile aggiornare ${actuatorId}`, "danger");
    logEvent(`Errore comando attuatore ${actuatorId}`, "danger");
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

    showToast("Regola creata", "Nuova regola salvata correttamente", "success");
    logEvent(`Creata regola su ${payload.sensor_name}.${payload.metric_name}`, "success");

    await loadRules();
  } catch (error) {
    console.error("Errore createRule:", error);
    showToast("Errore", "Impossibile creare la regola", "danger");
    logEvent("Errore creazione regola", "danger");
  }
}

async function toggleRule(ruleId, enabled) {
  try {
    await apiFetch(`${API_CONFIG.rules}/${ruleId}`, {
      method: "PUT",
      body: JSON.stringify({ enabled: !enabled })
    });

    showToast("Regola aggiornata", `Regola ${ruleId} aggiornata`, "success");
    logEvent(`Regola ${ruleId} ${enabled ? "disabilitata" : "abilitata"}`, "warning");

    await loadRules();
  } catch (error) {
    console.error("Errore toggleRule:", error);
    showToast("Errore", `Impossibile aggiornare la regola ${ruleId}`, "danger");
    logEvent(`Errore update regola ${ruleId}`, "danger");
  }
}

async function deleteRule(ruleId) {
  try {
    await apiFetch(`${API_CONFIG.rules}/${ruleId}`, {
      method: "DELETE"
    });

    showToast("Regola eliminata", `Regola ${ruleId} eliminata`, "warning");
    logEvent(`Regola ${ruleId} eliminata`, "warning");

    await loadRules();
  } catch (error) {
    console.error("Errore deleteRule:", error);
    showToast("Errore", `Impossibile eliminare la regola ${ruleId}`, "danger");
    logEvent(`Errore delete regola ${ruleId}`, "danger");
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

function resetRuleForm() {
  dom.ruleForm.reset();
  dom.ruleEnabledInput.checked = true;
}

async function handleRuleSubmit(event) {
  event.preventDefault();

  const payload = getRuleFormPayload();

  if (!payload.sensor_name || !payload.metric_name || Number.isNaN(payload.threshold)) {
    showToast("Form non valido", "Compila correttamente tutti i campi obbligatori", "warning");
    return;
  }

  await createRule(payload);

  const modalElement = document.getElementById("ruleModal");
  const modalInstance = bootstrap.Modal.getInstance(modalElement);
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
    showToast("Refresh", "Dashboard aggiornata", "info");
  });

  dom.ruleForm.addEventListener("submit", handleRuleSubmit);

 document.querySelectorAll(".actuator-toggle-btn").forEach(button => {
  button.addEventListener("click", () => {
    const actuatorId = button.dataset.actuator;
    const currentState = (appState.actuators[actuatorId] || "OFF").toUpperCase();
    const newState = currentState === "ON" ? "OFF" : "ON";

    sendActuatorCommand(actuatorId, newState);
  });
});

  document.addEventListener("click", async event => {
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
      const confirmed = confirm(`Eliminare la regola ${ruleId}?`);
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
    loadRules()
  ]);

  renderActuators();
  updateOverview();
}

/* =========================
   INIT
========================= */

async function init() {
  bindStaticEvents();

  logEvent("Frontend inizializzato", "info");

  await refreshDashboard();

  // Polling semplice ogni 10 secondi
  setInterval(async () => {
    await loadHealth();
    await loadLatestState();
  }, 10000);
}

document.addEventListener("DOMContentLoaded", init);