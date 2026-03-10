export async function createRule({
  payload,
  apiFetch,
  API_CONFIG,
  showToast,
  logEvent,
  loadRules
}) {
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

export async function updateRule({
  ruleId,
  payload,
  apiFetch,
  API_CONFIG,
  showToast,
  logEvent,
  loadRules
}) {
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

export async function toggleRule({
  ruleId,
  enabled,
  apiFetch,
  API_CONFIG,
  showToast,
  logEvent,
  loadRules
}) {
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

export async function deleteRule({
  ruleId,
  apiFetch,
  API_CONFIG,
  showToast,
  logEvent,
  loadRules
}) {
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

export async function resetRulesToDefault({
  apiFetch,
  API_CONFIG,
  showToast,
  logEvent,
  loadRules
}) {
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