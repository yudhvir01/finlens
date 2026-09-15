import { formatCurrency } from "../lib/format";
import type { CategoryBreakdownItem } from "../lib/types";

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)",
  "var(--chart-7)",
];
const FOLD_COLOR = "var(--chart-8)";
const MAX_SLOTS = 7;

export function CategoryBreakdown({ items }: { items: CategoryBreakdownItem[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No spending recorded for this month yet.</p>;
  }

  const visible = items.slice(0, MAX_SLOTS);
  const rest = items.slice(MAX_SLOTS);
  const otherTotal = rest.reduce((sum, i) => sum + Number(i.total), 0);
  const otherPct = rest.reduce((sum, i) => sum + i.percentage, 0);

  const rows = [
    ...visible.map((item, i) => ({ name: item.category_name, total: Number(item.total), pct: item.percentage, color: CHART_COLORS[i] })),
    ...(rest.length > 0 ? [{ name: "Other", total: otherTotal, pct: otherPct, color: FOLD_COLOR }] : []),
  ];

  return (
    <div>
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-muted">
        {rows.map((row, i) => (
          <div
            key={row.name}
            style={{ width: `${row.pct}%`, backgroundColor: row.color }}
            className={i > 0 ? "ml-0.5" : undefined}
            title={`${row.name}: ${row.pct}%`}
          />
        ))}
      </div>

      <ul className="mt-4 flex flex-col gap-2.5">
        {rows.map((row) => (
          <li key={row.name} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-foreground">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: row.color }} />
              {row.name}
            </span>
            <span className="flex items-center gap-3">
              <span className="font-mono-figures text-muted-foreground">{row.pct.toFixed(0)}%</span>
              <span className="font-mono-figures font-medium text-foreground">{formatCurrency(row.total)}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
