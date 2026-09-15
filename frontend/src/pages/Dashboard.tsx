import { useState } from "react";
import { Link } from "react-router-dom";
import { CashFlowChart } from "../components/CashFlowChart";
import { CategoryBreakdown } from "../components/CategoryBreakdown";
import { StatTile } from "../components/StatTile";
import { useAuth } from "../context/AuthProvider";
import { formatCurrency } from "../lib/format";
import { useCategoryBreakdown, useMonthly, useRecurring, useSummary } from "../hooks/useAnalytics";

function currentMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function shiftMonth(month: string, delta: number): string {
  const [y, m] = month.split("-").map(Number);
  const d = new Date(y, m - 1 + delta, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function monthLabel(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
}

export function Dashboard() {
  const { user } = useAuth();
  const [month, setMonth] = useState(currentMonth());

  const summary = useSummary(month);
  const monthly = useMonthly(6);
  const breakdown = useCategoryBreakdown(month);
  const recurring = useRecurring();

  const firstName = user?.full_name?.split(" ")[0] ?? user?.email.split("@")[0];
  const hasNoData = summary.data && Number(summary.data.income) === 0 && Number(summary.data.expenses) === 0;

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Good to see you, {firstName}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{monthLabel(month)}</h1>
        </div>
        <div className="inline-flex items-center gap-1 rounded-full border border-border p-1">
          <button
            type="button"
            onClick={() => setMonth((m) => shiftMonth(m, -1))}
            className="flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            aria-label="Previous month"
          >
            ‹
          </button>
          <button
            type="button"
            onClick={() => setMonth(currentMonth())}
            className="px-2 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            Today
          </button>
          <button
            type="button"
            onClick={() => setMonth((m) => shiftMonth(m, 1))}
            className="flex h-7 w-7 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            aria-label="Next month"
          >
            ›
          </button>
        </div>
      </header>

      {hasNoData && (
        <div className="rounded-xl border border-dashed border-border p-8 text-center">
          <p className="text-sm text-muted-foreground">No transactions for this month yet.</p>
          <Link
            to="/upload"
            className="mt-3 inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90"
          >
            Upload a statement
          </Link>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatTile label="Income" value={summary.data ? formatCurrency(summary.data.income) : "—"} tone="income" />
        <StatTile label="Expenses" value={summary.data ? formatCurrency(summary.data.expenses) : "—"} tone="expense" />
        <StatTile label="Net savings" value={summary.data ? formatCurrency(summary.data.net) : "—"} />
        <StatTile
          label="Savings rate"
          value={summary.data ? `${Math.round(summary.data.savings_rate * 100)}%` : "—"}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="rounded-xl border border-border bg-card p-5 lg:col-span-3">
          <h2 className="text-sm font-medium text-foreground">Cash flow — last 6 months</h2>
          <div className="mt-4">
            {monthly.data && <CashFlowChart points={monthly.data} />}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 lg:col-span-2">
          <h2 className="text-sm font-medium text-foreground">Spending by category</h2>
          <div className="mt-4">
            {breakdown.data && <CategoryBreakdown items={breakdown.data} />}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-5">
        <h2 className="text-sm font-medium text-foreground">Recurring expenses</h2>
        {recurring.data && recurring.data.length > 0 ? (
          <ul className="mt-4 flex flex-col divide-y divide-border">
            {recurring.data.map((item) => (
              <li key={item.merchant} className="flex items-center justify-between py-2.5 text-sm">
                <div>
                  <p className="font-medium text-foreground">{item.merchant}</p>
                  {item.category_name && <p className="text-xs text-muted-foreground">{item.category_name}</p>}
                </div>
                <div className="text-right">
                  <p className="font-mono-figures font-medium text-foreground">{formatCurrency(item.average_amount)}/mo</p>
                  <p className="text-xs text-muted-foreground">{item.occurrences} months</p>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-muted-foreground">
            Nothing recurring yet — Finlens looks for merchants that charge you at least twice.
          </p>
        )}
      </div>
    </div>
  );
}
