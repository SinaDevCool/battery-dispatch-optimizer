export function formatCurrency(value: unknown, currency = "EUR") {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return "-";
  }

  return new Intl.NumberFormat("en-GB", {
    currency,
    maximumFractionDigits: 0,
    style: "currency",
  }).format(numberValue);
}

export function formatNumber(value: unknown, digits = 2) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return "-";
  }

  return new Intl.NumberFormat("en-GB", {
    maximumFractionDigits: digits,
  }).format(numberValue);
}

export function formatDateTime(value: unknown) {
  if (!value) {
    return "-";
  }

  const date = new Date(String(value));

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}
