export function nowLabel() {
  return new Date().toLocaleTimeString("it-IT");
}

export function safeText(value, fallback = "--") {
  return value === null || value === undefined || value === "" ? fallback : value;
}

export function parseTimestamp(timestamp) {
  if (timestamp === null || timestamp === undefined || timestamp === "") {
    return null;
  }

  if (typeof timestamp === "number") {
    const ms = timestamp < 1e12 ? timestamp * 1000 : timestamp;
    const date = new Date(ms);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  const str = String(timestamp).trim();

  if (/^\d+$/.test(str)) {
    const numeric = Number(str);
    const ms = numeric < 1e12 ? numeric * 1000 : numeric;
    const date = new Date(ms);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  const normalized = str.replace(/\.(\d{3})\d+/, ".$1");
  const date = new Date(normalized);

  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatRelativeTime(timestamp) {
  const date = parseTimestamp(timestamp);
  if (!date) return "--";

  let diffSeconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (diffSeconds < 0) diffSeconds = 0;

  const hours = Math.floor(diffSeconds / 3600);
  const minutes = Math.floor((diffSeconds % 3600) / 60);
  const seconds = diffSeconds % 60;

  const mm = String(minutes).padStart(2, "0");
  const ss = String(seconds).padStart(2, "0");

  if (hours > 0) {
    const hh = String(hours).padStart(2, "0");
    return `${hh}:${mm}:${ss} ago`;
  }

  return `${mm}:${ss} ago`;
}

export function normalizeOperator(operator) {
  if (operator === "=") return "==";
  return operator;
}

export function evaluateRule(value, operator, threshold) {
  const numericValue = Number(value);
  const numericThreshold = Number(threshold);

  if (Number.isNaN(numericValue) || Number.isNaN(numericThreshold)) {
    return false;
  }

  switch (normalizeOperator(operator)) {
    case ">":
      return numericValue > numericThreshold;
    case "<":
      return numericValue < numericThreshold;
    case ">=":
      return numericValue >= numericThreshold;
    case "<=":
      return numericValue <= numericThreshold;
    case "==":
      return numericValue === numericThreshold;
    default:
      return false;
  }
}

export function isRuleEnabled(rule) {
  return rule.enabled === true || rule.enabled === 1;
}

export function statusClass(status) {
  const normalized = String(status || "").toLowerCase();

  if (normalized.includes("ok") || normalized.includes("on")) return "status-ok";
  if (normalized.includes("warn")) return "status-warning";
  if (
    normalized.includes("error") ||
    normalized.includes("fail") ||
    normalized.includes("off")
  ) {
    return "status-error";
  }

  return "status-unknown";
}

export function sanitizeGroupKey(value) {
  return String(value).replace(/[^a-zA-Z0-9_-]/g, "_");
}