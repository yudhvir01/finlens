const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const compactCurrencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  notation: "compact",
  maximumFractionDigits: 1,
});

export function formatCurrency(value: string | number): string {
  return currencyFormatter.format(Number(value));
}

export function formatCurrencyCompact(value: string | number): string {
  return compactCurrencyFormatter.format(Number(value));
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

export function formatMonth(month: string): string {
  const [year, mon] = month.split("-").map(Number);
  return new Date(year, mon - 1, 1).toLocaleDateString("en-IN", { month: "short", year: "2-digit" });
}
