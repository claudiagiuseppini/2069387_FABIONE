export const STREAM_CONFIG = {
  fallbackPollingMs: 10000
};

export function stopFallbackPolling(streamState) {
  if (streamState.fallbackTimer) {
    clearInterval(streamState.fallbackTimer);
    streamState.fallbackTimer = null;
  }
}

export function startFallbackPolling({
  streamState,
  loadHealth,
  loadLatestState,
  loadActuators,
  fallbackPollingMs = STREAM_CONFIG.fallbackPollingMs
}) {
  if (streamState.fallbackTimer) return;

  streamState.fallbackTimer = setInterval(async () => {
    await loadHealth();
    await loadLatestState();
    await loadActuators();
  }, fallbackPollingMs);
}

export function closeDashboardStream(streamState) {
  if (streamState.source) {
    streamState.source.close();
    streamState.source = null;
  }

  streamState.connected = false;
}

export function startDashboardStream({
  streamState,
  dashboardStreamUrl,
  applyDashboardSnapshot,
  logEvent,
  loadHealth,
  loadLatestState,
  loadActuators
}) {
  if (typeof EventSource === "undefined") {
    startFallbackPolling({
      streamState,
      loadHealth,
      loadLatestState,
      loadActuators
    });
    return;
  }

  closeDashboardStream(streamState);

  const source = new EventSource(dashboardStreamUrl);
  streamState.source = source;

  source.onopen = () => {
    const firstConnect = !streamState.connected;
    streamState.connected = true;
    stopFallbackPolling(streamState);

    if (firstConnect) {
      logEvent("SSE connesso: aggiornamenti real-time attivi", "success");
    }
  };

  source.onmessage = event => {
    try {
      const snapshot = JSON.parse(event.data);
      applyDashboardSnapshot(snapshot);
    } catch (error) {
      console.error("Errore parsing evento SSE:", error);
    }
  };

  source.onerror = () => {
    if (streamState.connected) {
      logEvent("SSE disconnesso: attivo fallback polling", "warning");
      streamState.connected = false;
    }

    startFallbackPolling({
      streamState,
      loadHealth,
      loadLatestState,
      loadActuators
    });
  };
}