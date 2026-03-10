export function getRuleFormPayload(dom) {
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

export function setRuleFormModeEditing({
  rule,
  appState,
  dom,
  ruleModalElements,
  safeText,
  isRuleEnabled
}) {
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

export function setRuleFormModeCreate({
  appState,
  ruleModalElements
}) {
  appState.editingRuleId = null;
  ruleModalElements.title.textContent = "Create Automation Rule";
  ruleModalElements.submitButton.textContent = "Save Rule";
}

export function resetRuleForm({
  dom,
  appState,
  ruleModalElements
}) {
  dom.ruleForm.reset();
  dom.ruleEnabledInput.checked = true;

  setRuleFormModeCreate({
    appState,
    ruleModalElements
  });
}

export function openEditRuleModal({
  ruleId,
  appState,
  ruleModalElements,
  dom,
  safeText,
  isRuleEnabled,
  showToast
}) {
  const rule = appState.rules.find(item => String(item.id) === String(ruleId));

  if (!rule) {
    showToast("Errore", `Rule ${ruleId} not found`, "danger");
    return;
  }

  setRuleFormModeEditing({
    rule,
    appState,
    dom,
    ruleModalElements,
    safeText,
    isRuleEnabled
  });

  const modal = bootstrap.Modal.getOrCreateInstance(ruleModalElements.modal);
  modal.show();
}

export async function handleRuleSubmit({
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
}) {
  event.preventDefault();

  const payload = getRuleFormPayload(dom);

  if (!payload.sensor_name || !payload.metric_name || Number.isNaN(payload.threshold)) {
    showToast("Form not valid", "Fill all mandatory entries", "warning");
    return;
  }

  const submitOk = appState.editingRuleId === null
    ? await createRule({
        payload,
        apiFetch,
        API_CONFIG,
        showToast,
        logEvent,
        loadRules
      })
    : await updateRule({
        ruleId: appState.editingRuleId,
        payload,
        apiFetch,
        API_CONFIG,
        showToast,
        logEvent,
        loadRules
      });

  if (!submitOk) {
    return;
  }

  const modalInstance = bootstrap.Modal.getInstance(ruleModalElements.modal);
  if (modalInstance) {
    modalInstance.hide();
  }

  resetRuleForm({
    dom,
    appState,
    ruleModalElements
  });
}