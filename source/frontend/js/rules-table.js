export function renderRulesTable({
  rules,
  rulesTableBody,
  safeText,
  isRuleEnabled
}) {
  if (!rules.length) {
    rulesTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-secondary py-4">
          Nessuna regola caricata
        </td>
      </tr>
    `;
    return;
  }

  const html = rules.map(rule => {
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

  rulesTableBody.innerHTML = html;
}