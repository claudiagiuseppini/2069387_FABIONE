export function showToast(title, message, type = "info") {
  const toastContainer = document.getElementById("toast-container");
  if (!toastContainer) return;

  const toastId = `toast-${Date.now()}`;

  let borderClass = "border-info";
  if (type === "success") borderClass = "border-success";
  if (type === "warning") borderClass = "border-warning";
  if (type === "danger" || type === "error") borderClass = "border-danger";

  const timeLabel = new Date().toLocaleTimeString("it-IT");

  const toastHtml = `
    <div id="${toastId}" class="toast ${borderClass}" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="toast-header">
        <strong class="me-auto">${title}</strong>
        <small class="text-secondary">${timeLabel}</small>
        <button type="button" class="btn-close btn-close-white ms-2 mb-1" data-bs-dismiss="toast" aria-label="Chiudi"></button>
      </div>
      <div class="toast-body">
        ${message}
      </div>
    </div>
  `;

  toastContainer.insertAdjacentHTML("beforeend", toastHtml);

  const toastElement = document.getElementById(toastId);
  if (!toastElement) return;

  const toast = new bootstrap.Toast(toastElement, { delay: 4000 });
  toast.show();

  toastElement.addEventListener("hidden.bs.toast", () => {
    toastElement.remove();
  });
}

export function scrollToAlertsSection() {
  const alertsSection = document.getElementById("alerts-event-stream");
  if (!alertsSection) return;

  alertsSection.scrollIntoView({
    behavior: "smooth",
    block: "center"
  });
}

export function highlightAlertsCard() {
  const alertsEventCard = document.getElementById("alerts-event-card");
  if (!alertsEventCard) return;

  alertsEventCard.classList.remove("alerts-card-highlight");

  void alertsEventCard.offsetWidth;

  alertsEventCard.classList.add("alerts-card-highlight");

  window.setTimeout(() => {
    alertsEventCard.classList.remove("alerts-card-highlight");
  }, 1200);
}

export function askForConfirmation({
  title = "Confirm action",
  message = "Are you sure?",
  confirmLabel = "Confirm",
  confirmButtonClass = "btn btn-warning text-dark fw-semibold"
} = {}) {
  const confirmModal = document.getElementById("confirmActionModal");
  const confirmTitle = document.getElementById("confirmActionModalLabel");
  const confirmMessage = document.getElementById("confirm-action-message");
  const confirmOkButton = document.getElementById("confirm-action-ok-btn");

  if (!confirmModal || !confirmOkButton || !confirmTitle || !confirmMessage) {
    showToast("Errore UI", "Confirmation dialog unavailable", "danger");
    return Promise.resolve(false);
  }

  confirmTitle.textContent = title;
  confirmMessage.textContent = message;
  confirmOkButton.textContent = confirmLabel;
  confirmOkButton.className = confirmButtonClass;

  const modal = bootstrap.Modal.getOrCreateInstance(confirmModal);

  return new Promise(resolve => {
    let confirmed = false;

    const onConfirmClick = () => {
      confirmed = true;
      modal.hide();
    };

    const onHidden = () => {
      confirmOkButton.removeEventListener("click", onConfirmClick);
      confirmModal.removeEventListener("hidden.bs.modal", onHidden);
      resolve(confirmed);
    };

    confirmOkButton.addEventListener("click", onConfirmClick);
    confirmModal.addEventListener("hidden.bs.modal", onHidden, { once: true });

    modal.show();
  });
}