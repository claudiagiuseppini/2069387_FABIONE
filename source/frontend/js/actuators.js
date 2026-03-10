export function renderActuators({ appState, actuatorElements }) {
  Object.entries(actuatorElements).forEach(([actuatorId, config]) => {
    const state = String(appState.actuators[actuatorId] || "OFF").toUpperCase();
    const isOn = state === "ON";

    if (config.state) {
      config.state.textContent = state;
      config.state.className = isOn
        ? "badge rounded-pill text-bg-success"
        : "badge rounded-pill text-bg-secondary";
    }

    if (config.button) {
      config.button.textContent = isOn ? "ON" : "OFF";
      config.button.className = isOn
        ? "btn btn-sm btn-outline-success actuator-toggle-btn"
        : "btn btn-sm btn-outline-danger actuator-toggle-btn";
    }

    if (config.icon) {
      config.icon.classList.toggle("actuator-icon-on", isOn);
      config.icon.classList.toggle("actuator-icon-off", !isOn);
    }
  });
}

export async function sendActuatorCommand({
  actuatorId,
  state,
  appState,
  actuatorElements,
  apiFetch,
  API_CONFIG,
  showToast,
  logEvent,
  updateOverview
}) {
  try {
    await apiFetch(`${API_CONFIG.actuators}/${actuatorId}`, {
      method: "POST",
      body: JSON.stringify({ state })
    });

    appState.actuators[actuatorId] = state;

    renderActuators({
      appState,
      actuatorElements
    });

    updateOverview();

    showToast("Actuator", `${actuatorId} set on ${state}`, "success");
    logEvent(`Actuator Command: ${actuatorId} -> ${state}`, "success");
    return true;
  } catch (error) {
    console.error("Errore sendActuatorCommand:", error);
    showToast("Errore", `Impossible to load ${actuatorId}`, "danger");
    logEvent(`Error command actuator ${actuatorId}`, "danger");
    return false;
  }
}

export async function resetActuatorsToDefault({
  appState,
  actuatorElements,
  apiFetch,
  API_CONFIG,
  showToast,
  logEvent,
  loadActuators,
  updateOverview
}) {
  try {
    const response = await apiFetch(API_CONFIG.resetActuators, {
      method: "POST"
    });

    const resetCount = Number(response?.reset_count || 0);

    Object.keys(appState.actuators).forEach(actuatorId => {
      appState.actuators[actuatorId] = "OFF";
    });

    renderActuators({
      appState,
      actuatorElements
    });

    updateOverview();

    showToast("Reset actuators", `${resetCount} attuatori impostati su OFF`, "warning");
    logEvent(`Reset attuatori: ${resetCount} attuatori su OFF`, "warning");

    await loadActuators();
    return true;
  } catch (error) {
    console.error("Errore resetActuatorsToDefault:", error);
    showToast("Errore", "Impossible to reset actuators to OFF", "danger");
    logEvent("Errore reset attuatori", "danger");
    return false;
  }
}

export function bindActuatorActions({
  appState,
  actuatorButtonsSelector = ".actuator-toggle-btn",
  apiFetch,
  API_CONFIG,
  showToast,
  logEvent,
  updateOverview,
  actuatorElements
}) {
  document.querySelectorAll(actuatorButtonsSelector).forEach(button => {
    button.addEventListener("click", async () => {
      const actuatorId = button.dataset.actuator;
      const currentState = String(appState.actuators[actuatorId] || "OFF").toUpperCase();
      const newState = currentState === "ON" ? "OFF" : "ON";

      await sendActuatorCommand({
        actuatorId,
        state: newState,
        appState,
        actuatorElements,
        apiFetch,
        API_CONFIG,
        showToast,
        logEvent,
        updateOverview
      });
    });
  });
}