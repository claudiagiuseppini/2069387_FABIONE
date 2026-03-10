export function bindRuleActions({
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
}) {
  document.addEventListener("click", async event => {
    const editBtn = event.target.closest(".edit-rule-btn");
    if (editBtn) {
      openEditRuleModal({
        ruleId: editBtn.dataset.id,
        appState,
        ruleModalElements,
        dom,
        safeText,
        isRuleEnabled,
        showToast
      });
      return;
    }

    const toggleBtn = event.target.closest(".toggle-rule-btn");
    if (toggleBtn) {
      const ruleId = toggleBtn.dataset.id;
      const enabled = toggleBtn.dataset.enabled === "true";

      await toggleRule({
        ruleId,
        enabled,
        apiFetch,
        API_CONFIG,
        showToast,
        logEvent,
        loadRules
      });
      return;
    }

    const deleteBtn = event.target.closest(".delete-rule-btn");
    if (deleteBtn) {
      const ruleId = deleteBtn.dataset.id;

      const confirmed = await askForConfirmation({
        title: "Delete rule",
        message: `Deleting rule ${ruleId}?`,
        confirmLabel: "Delete",
        confirmButtonClass: "btn btn-danger fw-semibold"
      });

      if (!confirmed) return;

      await deleteRule({
        ruleId,
        apiFetch,
        API_CONFIG,
        showToast,
        logEvent,
        loadRules
      });
    }
  });
}