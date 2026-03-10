export function extractLatestSensors(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.latest)) return data.latest;
  if (Array.isArray(data?.data)) return data.data;
  return [];
}

export function mergeActuatorStates(currentActuators, data) {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return currentActuators;
  }

  return {
    ...currentActuators,
    ...Object.fromEntries(
      Object.entries(data).map(([key, value]) => [
        key,
        String(value || "OFF").toUpperCase()
      ])
    )
  };
}