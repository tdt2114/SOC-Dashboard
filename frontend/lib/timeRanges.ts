export const TIME_RANGE_OPTIONS = [
  { value: "1h", label: "Last 1h", shortLabel: "1h" },
  { value: "24h", label: "Last 24h", shortLabel: "24h" },
  { value: "3day", label: "Last 3 days", shortLabel: "3day" },
  { value: "7d", label: "Last 7 days", shortLabel: "7d" },
  { value: "1m", label: "Last 1 month", shortLabel: "1m" },
  { value: "3m", label: "Last 3 months", shortLabel: "3m" }
];

export function normalizeTimeRange(value?: string | null) {
  const normalized = (value || "24h").trim().toLowerCase();
  return TIME_RANGE_OPTIONS.some((option) => option.value === normalized) ? normalized : "24h";
}

export function getTimeRangeLabel(value: string) {
  return TIME_RANGE_OPTIONS.find((option) => option.value === value)?.label || "Last 24h";
}

export function getTimeRangeShortLabel(value: string) {
  return TIME_RANGE_OPTIONS.find((option) => option.value === value)?.shortLabel || "24h";
}
