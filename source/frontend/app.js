import {
  nowLabel,
  safeText,
  parseTimestamp,
  formatRelativeTime,
  normalizeOperator,
  evaluateRule,
  isRuleEnabled,
  statusClass,
  sanitizeGroupKey
} from "./js/utils.js";

import { API_CONFIG, apiFetch } from "./js/api.js";

import {
  chartState,
  initChart,
  updateChartForSelectedMetric,
  appendPointToChartHistory,
  addSensorToChartHistory
} from "./js/chart.js";

import { appState, streamState, alertState } from "./js/state.js";

import {
  SENSOR_GROUPS,
  groupSensorsByCategories,
  buildMetricRow,
  bindSensorGroupToggles,
  populateChartSelect,
  renderSensorCards
} from "./js/sensors.js";

import {
  STREAM_CONFIG,
  stopFallbackPolling,
  startFallbackPolling,
  closeDashboardStream,
  startDashboardStream
} from "./js/stream.js";

import {
  createRule,
  updateRule,
  toggleRule,
  deleteRule,
  resetRulesToDefault
} from "./js/rules-api.js";

import {
  getRuleFormPayload,
  setRuleFormModeEditing,
  openEditRuleModal,
  setRuleFormModeCreate,
  resetRuleForm,
  handleRuleSubmit
} from "./js/rules-form.js";

import { renderRulesTable } from "./js/rules-table.js";

import { bindRuleActions } from "./js/rules-actions-ui.js";

import {
  renderActuators,
  sendActuatorCommand,
  resetActuatorsToDefault,
  bindActuatorActions
} from "./js/actuators.js";

import {
  showToast,
  scrollToAlertsSection,
  highlightAlertsCard,
  askForConfirmation
} from "./js/ui-feedback.js";

import {
  updateOverview,
  renderEventLog,
  updateSystemBadge
} from "./js/overview.js";

import {
  extractLatestSensors,
  mergeActuatorStates
} from "./js/dashboard-data.js";

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
  alertsJumpButton: document.getElementById("alerts-jump-btn"),
  alertsSection: document.getElementById("alerts-event-stream"),
  alertsEventCard: document.getElementById("alerts-event-card"),
  chartSensorSelect: document.getElementById("chart-sensor-select"),

  refreshButton: document.getElementById("refresh-dashboard-btn"),
  resetRulesButton: document.getElementById("reset-rules-btn"),
  resetActuatorsButton: document.getElementById("reset-actuators-btn"),
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

const confirmModalElements = {
  modal: document.getElementById("confirmActionModal"),
  title: document.getElementById("confirmActionModalLabel"),
  message: document.getElementById("confirm-action-message"),
  okButton: document.getElementById("confirm-action-ok-btn")
};

const confirmModalState = {
  resolver: null,
  confirmed: false
};

const actuatorElements = {
  cooling_fan: {
    button: document.querySelector('.actuator-toggle-btn[data-actuator="cooling_fan"]'),
    icon: document.querySelector('[data-actuator-icon="cooling_fan"]')
  },
  entrance_humidifier: {
    button: document.querySelector('.actuator-toggle-btn[data-actuator="entrance_humidifier"]'),
    icon: document.querySelector('[data-actuator-icon="entrance_humidifier"]')
  },
  hall_ventilation: {
    button: document.querySelector('.actuator-toggle-btn[data-actuator="hall_ventilation"]'),
    icon: document.querySelector('[data-actuator-icon="hall_ventilation"]')
  },
  habitat_heater: {
    button: document.querySelector('.actuator-toggle-btn[data-actuator="habitat_heater"]'),
    icon: document.querySelector('[data-actuator-icon="habitat_heater"]')
  }
};

/* =========================
   HELPERS
========================= */

function refreshOverviewUI() {
  updateOverview({
    appState,
    dom,
    groupSensorsByCategories,
    isRuleEnabled,
    nowLabel
  });
}

function getSensorRuleViolations(sensor) {
  return appState.rules.filter(rule => {
    if (!isRuleEnabled(rule)) return false;

    const sameSensor =
      String(rule.sensor_name || "").trim() === String(sensor.sensor_id || "").trim();

    const sameMetric =
      String(rule.metric_name || "").trim() === String(sensor.metric_name || "").trim();

    if (!sameSensor || !sameMetric) return false;

    return evaluateRule(sensor.value, rule.operator, rule.threshold);
  });
}

function doesSensorViolateRules(sensor) {
  return getSensorRuleViolations(sensor).length > 0;
}

function buildViolationKey(sensor, rule) {
  const ruleId = safeText(rule.id, "no-id");
  return `${ruleId}|${safeText(sensor.sensor_id)}|${safeText(sensor.metric_name)}`;
}

function syncRuleViolationEvents() {
  const currentViolations = new Map();

  appState.latestSensors.forEach(sensor => {
    const violatedRules = getSensorRuleViolations(sensor);

    violatedRules.forEach(rule => {
      const key = buildViolationKey(sensor, rule);

      currentViolations.set(key, {
        rule,
        sensor,
        value: safeText(sensor.value),
        unit: safeText(sensor.unit, "")
      });
    });
  });

  currentViolations.forEach((details, key) => {
    if (!alertState.activeViolationKeys.has(key)) {
      const condition = `${safeText(details.rule.operator)} ${safeText(details.rule.threshold)}`;
      const valueText = `${details.value}${details.unit ? ` ${details.unit}` : ""}`;

      logEvent(
        `Rule violated: ${safeText(details.sensor.sensor_id)}.${safeText(details.sensor.metric_name)} = ${valueText} (${condition})`,
        "danger"
      );
    }
  });

  alertState.activeViolationKeys.forEach(key => {
    if (!currentViolations.has(key)) {
      const previous = alertState.activeViolationDetails.get(key);
      const sensorLabel = previous
        ? `${safeText(previous.sensor.sensor_id)}.${safeText(previous.sensor.metric_name)}`
        : "sensor.metric";

      logEvent(`Violation resolved: ${sensorLabel}`, "success");
    }
  });

  alertState.activeViolationKeys = new Set(currentViolations.keys());
  alertState.activeViolationDetails = currentViolations;
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
  renderEventLog({
    eventLog: appState.eventLog,
    eventLogList: dom.eventLogList
  });
}

/* =========================
   FETCH DATA
========================= */

async function loadLatestState() {
  try {
    const data = await apiFetch(API_CONFIG.latestState);

appState.latestSensors = extractLatestSensors(data);

appState.latestSensors.forEach(sensor => {
  addSensorToChartHistory(sensor);
});

renderSensorCards({
  latestSensors: appState.latestSensors,
  sensorCardsContainer: dom.sensorCardsContainer,
  chartSensorSelect: dom.chartSensorSelect,
  appState,
  chartState,
  helpers: {
    sanitizeGroupKey,
    buildMetricRowHelpers: {
      safeText,
      formatRelativeTime,
      statusClass,
      doesSensorViolateRules
    }
  }
});
refreshOverviewUI();
syncRuleViolationEvents();

if (chartState.selectedMetricKey) {
  updateChartForSelectedMetric();
}

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

    renderRulesTable({
      rules: appState.rules,
      rulesTableBody: dom.rulesTableBody,
      safeText,
      isRuleEnabled
    });

    renderSensorCards({
      latestSensors: appState.latestSensors,
      sensorCardsContainer: dom.sensorCardsContainer,
      chartSensorSelect: dom.chartSensorSelect,
      appState,
      chartState,
      helpers: {
        sanitizeGroupKey,
        buildMetricRowHelpers: {
          safeText,
          formatRelativeTime,
          statusClass,
          doesSensorViolateRules
        }
      }
    });    
    refreshOverviewUI();
    syncRuleViolationEvents();

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
    updateSystemBadge({
      data,
      systemStatusBadge: dom.systemStatusBadge
    });
  } catch (error) {
    dom.systemStatusBadge.textContent = "System Offline";
    dom.systemStatusBadge.className = "badge rounded-pill text-bg-danger";
  }
}

async function loadActuators() {
  try {
    const data = await apiFetch(API_CONFIG.actuators);

    appState.actuators = mergeActuatorStates(appState.actuators, data);

    renderActuators({
      appState,
      actuatorElements
    });
    refreshOverviewUI();
  } catch (error) {
    console.error("Errore loadActuators:", error);
    logEvent("Errore caricamento attuatori", "danger");
  }
}

function applyDashboardSnapshot(snapshot) {
  const nextLatestSensors = extractLatestSensors(snapshot?.latest);

if (nextLatestSensors.length > 0) {
  appState.latestSensors = nextLatestSensors;

  appState.latestSensors.forEach(sensor => {
    addSensorToChartHistory(sensor);
  });

  renderSensorCards({
  latestSensors: appState.latestSensors,
  sensorCardsContainer: dom.sensorCardsContainer,
  chartSensorSelect: dom.chartSensorSelect,
  appState,
  chartState,
  helpers: {
    sanitizeGroupKey,
    buildMetricRowHelpers: {
      safeText,
      formatRelativeTime,
      statusClass,
      doesSensorViolateRules
    }
  }
});
  syncRuleViolationEvents();

  if (chartState.selectedMetricKey) {
    updateChartForSelectedMetric();
  }
}

  const mergedActuators = mergeActuatorStates(appState.actuators, snapshot.actuators);

if (mergedActuators !== appState.actuators) {
  appState.actuators = mergedActuators;
    renderActuators({
      appState,
      actuatorElements
    });
  }

  if (snapshot.health && typeof snapshot.health === "object") {
    updateSystemBadge({
      data: snapshot.health,
      systemStatusBadge: dom.systemStatusBadge
    });
  }

  refreshOverviewUI();
}

/* =========================
   EVENTS BINDING
========================= */

function bindStaticEvents() {

  dom.chartSensorSelect?.addEventListener("change", (event) => {
  chartState.selectedMetricKey = event.target.value;
  updateChartForSelectedMetric();
});

  dom.refreshButton.addEventListener("click", async () => {
    await refreshDashboard();
    showToast("Refresh", "Dashboard refreshed", "info");
  });

  if (dom.alertsJumpButton) {
    dom.alertsJumpButton.addEventListener("click", event => {
      event.preventDefault();
      scrollToAlertsSection();
      highlightAlertsCard();
    });
  }

  if (dom.resetRulesButton) {
    dom.resetRulesButton.addEventListener("click", async () => {
      const confirmed = await askForConfirmation({
        title: "Reset default rules",
        message: "Ripristinare tutte le regole ai valori di default? Questa azione sovrascrive modifiche, aggiunte e cancellazioni.",
        confirmLabel: "Reset rules",
        confirmButtonClass: "btn btn-warning text-dark fw-semibold"
      });
      if (!confirmed) return;
      await resetRulesToDefault({
        apiFetch,
        API_CONFIG,
        showToast,
        logEvent,
        loadRules
      });
    });
  }

  if (dom.resetActuatorsButton) {
    dom.resetActuatorsButton.addEventListener("click", async () => {
      const confirmed = await askForConfirmation({
        title: "Reset actuators",
        message: "Impostare tutti gli attuatori a OFF (default)?",
        confirmLabel: "Set OFF",
        confirmButtonClass: "btn btn-warning text-dark fw-semibold"
      });
      if (!confirmed) return;
      await resetActuatorsToDefault({
        appState,
        actuatorElements,
        apiFetch,
        API_CONFIG,
        showToast,
        logEvent,
        loadActuators,
        updateOverview: refreshOverviewUI
      });
    });
  }

  dom.ruleForm.addEventListener("submit", async event => {
    await handleRuleSubmit({
      event,
      appState,
      dom,
      ruleModalElements,
      createRule,
      updateRule,
      apiFetch,
      API_CONFIG,
      showToast,
      logEvent,
      loadRules
    });
  });

  ruleModalElements.modal.addEventListener("hidden.bs.modal", () => {
    resetRuleForm({
      dom,
      appState,
      ruleModalElements
    });
  });

  ruleModalElements.modal.addEventListener("show.bs.modal", event => {
    const opener = event.relatedTarget;
    if (opener && opener.hasAttribute("data-create-rule")) {
      resetRuleForm({
        dom,
        appState,
        ruleModalElements
      });
    }
  });

  bindActuatorActions({
    appState,
    apiFetch,
    API_CONFIG,
    showToast,
    logEvent,
    updateOverview: refreshOverviewUI,
    actuatorElements
  });

    bindRuleActions({
    appState,
    ruleModalElements,
    dom,
    safeText,
    isRuleEnabled,
    showToast,
    openEditRuleModal,
    toggleRule,
    deleteRule,
    askForConfirmation,
    apiFetch,
    API_CONFIG,
    logEvent,
    loadRules
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

  renderActuators({
    appState,
    actuatorElements
  });
  refreshOverviewUI();
}

/* =========================
   INIT
========================= */

async function init() {
  bindStaticEvents();

  initChart();

  logEvent("Initialized frontend", "info");

  await refreshDashboard();
  startDashboardStream({
  streamState,
  dashboardStreamUrl: API_CONFIG.dashboardStream,
  applyDashboardSnapshot,
  logEvent,
  loadHealth,
  loadLatestState,
  loadActuators
});
}

document.addEventListener("DOMContentLoaded", init);