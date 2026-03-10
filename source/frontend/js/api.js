export const API_BASE = "http://localhost:8000";

export const API_CONFIG = {
  latestState: `${API_BASE}/api/latest`,
  rules: `${API_BASE}/api/rules`,
  resetRules: `${API_BASE}/api/rules/reset`,
  actuators: `${API_BASE}/api/actuators`,
  resetActuators: `${API_BASE}/api/actuators/reset`,
  events: `${API_BASE}/api/events`,
  health: `${API_BASE}/api/health`,
  dashboardStream: `${API_BASE}/api/stream/dashboard`
};

export async function apiFetch(url, options = {}) {
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