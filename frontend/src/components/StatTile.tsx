export function StatTile({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "income" | "expense";
}) {
  const toneClass = tone === "income" ? "text-income" : tone === "expense" ? "text-expense" : "text-foreground";

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className={`mt-1.5 text-2xl font-semibold tracking-tight ${toneClass}`}>{value}</p>
    </div>
  );
}
