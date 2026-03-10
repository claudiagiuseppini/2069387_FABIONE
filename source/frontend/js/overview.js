export function updateOverview({
  appState,
  dom,
  groupSensorsByCategories,
  isRuleEnabled,
  nowLabel
}) {
  const uniqueSensorIds = new Set(appState.latestSensors.map(s => s.sensor_id));
  dom.activeSensorsCount.textContent = uniqueSensorIds.size;

  const groupedSensors = groupSensorsByCategories(appState.latestSensors);
  dom.sensorCardsBadge.textContent = `${groupedSensors.length} categories · ${appState.latestSensors.length} metrics`;

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

export function renderEventLog({
  eventLog,
  eventLogList
}) {
  if (!eventLog.length) {
    eventLogList.innerHTML = `
      <li class="list-group-item bg-black text-secondary border-secondary">
        Nessun evento disponibile
      </li>
    `;
    return;
  }

  const html = eventLog.map(event => `
    <li class="list-group-item border-secondary">
      <div class="text-white event-item event-${event.type}">
        <div class="text-white fw-semibold">${event.message}</div>
        <div class="text-white event-time">${event.time}</div>
      </div>
    </li>
  `).join("");

  eventLogList.innerHTML = html;
}

export function updateSystemBadge({
  data,
  systemStatusBadge
}) {
  const ok = data?.status || data?.ok || data?.service;
  systemStatusBadge.textContent = ok ? "System Online" : "System Degraded";
  systemStatusBadge.className = ok
    ? "badge rounded-pill text-bg-success"
    : "badge rounded-pill text-bg-danger";
}