export const appState = {
  latestSensors: [],
  rules: [],
  editingRuleId: null,
  actuators: {
    cooling_fan: "OFF",
    entrance_humidifier: "OFF",
    hall_ventilation: "OFF",
    habitat_heater: "OFF"
  },
  eventLog: [],
  openGroups: new Set(["priority"])
};

export const streamState = {
  source: null,
  fallbackTimer: null,
  connected: false
};

export const alertState = {
  activeViolationKeys: new Set(),
  activeViolationDetails: new Map()
};