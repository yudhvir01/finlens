import { useId, useMemo, useState } from "react";
import { formatCurrencyCompact, formatMonth } from "../lib/format";
import type { MonthlyPoint } from "../lib/types";

const WIDTH = 720;
const HEIGHT = 240;
const PAD_LEFT = 44;
const PAD_RIGHT = 16;
const PAD_TOP = 16;
const PAD_BOTTOM = 28;

function niceTicks(max: number, count = 4): number[] {
  if (max <= 0) return [0];
  const rough = max / count;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const residual = rough / magnitude;
  const step = (residual >= 5 ? 5 : residual >= 2 ? 2 : 1) * magnitude;
  const ticks: number[] = [];
  for (let v = 0; v <= max + step; v += step) ticks.push(v);
  return ticks;
}

export function CashFlowChart({ points }: { points: MonthlyPoint[] }) {
  const clipId = useId();
  const [hover, setHover] = useState<number | null>(null);

  const values = useMemo(
    () => points.map((p) => ({ income: Number(p.income), expenses: Number(p.expenses) })),
    [points],
  );
  const maxValue = Math.max(1, ...values.map((v) => Math.max(v.income, v.expenses)));
  const ticks = niceTicks(maxValue);
  const tickMax = ticks[ticks.length - 1];

  const innerWidth = WIDTH - PAD_LEFT - PAD_RIGHT;
  const innerHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;

  const xFor = (i: number) => PAD_LEFT + (points.length === 1 ? innerWidth / 2 : (i / (points.length - 1)) * innerWidth);
  const yFor = (v: number) => PAD_TOP + innerHeight - (v / tickMax) * innerHeight;

  const pathFor = (key: "income" | "expenses") =>
    values.map((v, i) => `${i === 0 ? "M" : "L"}${xFor(i)},${yFor(v[key])}`).join(" ");

  function handleMove(e: React.MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const relX = ((e.clientX - rect.left) / rect.width) * WIDTH;
    const t = Math.min(1, Math.max(0, (relX - PAD_LEFT) / innerWidth));
    const idx = Math.round(t * (points.length - 1));
    setHover(Math.min(points.length - 1, Math.max(0, idx)));
  }

  const hoverPoint = hover !== null ? points[hover] : null;
  const hoverX = hover !== null ? xFor(hover) : 0;

  return (
    <div className="relative">
      <div className="mb-3 flex items-center gap-4 text-xs">
        <span className="inline-flex items-center gap-1.5 text-muted-foreground">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--income)" }} />
          Income
        </span>
        <span className="inline-flex items-center gap-1.5 text-muted-foreground">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: "var(--expense)" }} />
          Expenses
        </span>
      </div>

      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="w-full touch-none"
        onMouseMove={handleMove}
        onMouseLeave={() => setHover(null)}
        role="img"
        aria-label="Monthly income vs expenses"
      >
        <defs>
          <clipPath id={clipId}>
            <rect x={PAD_LEFT} y={PAD_TOP} width={innerWidth} height={innerHeight} />
          </clipPath>
        </defs>

        {ticks.map((t) => (
          <g key={t}>
            <line
              x1={PAD_LEFT}
              x2={WIDTH - PAD_RIGHT}
              y1={yFor(t)}
              y2={yFor(t)}
              stroke="var(--chart-gridline)"
              strokeWidth={1}
            />
            <text x={PAD_LEFT - 8} y={yFor(t)} textAnchor="end" dominantBaseline="middle" className="fill-muted-foreground" fontSize={10}>
              {formatCurrencyCompact(t)}
            </text>
          </g>
        ))}

        <line
          x1={PAD_LEFT}
          x2={WIDTH - PAD_RIGHT}
          y1={PAD_TOP + innerHeight}
          y2={PAD_TOP + innerHeight}
          stroke="var(--chart-baseline)"
          strokeWidth={1}
        />

        {points.map((p, i) => (
          <text
            key={p.month}
            x={xFor(i)}
            y={HEIGHT - 8}
            textAnchor="middle"
            className="fill-muted-foreground"
            fontSize={10}
          >
            {formatMonth(p.month)}
          </text>
        ))}

        <g clipPath={`url(#${clipId})`}>
          <path d={pathFor("expenses")} fill="none" stroke="var(--expense)" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
          <path d={pathFor("income")} fill="none" stroke="var(--income)" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        </g>

        {values.length > 0 && (
          <>
            <circle cx={xFor(values.length - 1)} cy={yFor(values[values.length - 1].income)} r={4} fill="var(--income)" stroke="var(--card)" strokeWidth={2} />
            <circle cx={xFor(values.length - 1)} cy={yFor(values[values.length - 1].expenses)} r={4} fill="var(--expense)" stroke="var(--card)" strokeWidth={2} />
          </>
        )}

        {hover !== null && (
          <line x1={hoverX} x2={hoverX} y1={PAD_TOP} y2={PAD_TOP + innerHeight} stroke="var(--chart-baseline)" strokeWidth={1} strokeDasharray="3,3" />
        )}
        {hover !== null && (
          <>
            <circle cx={hoverX} cy={yFor(values[hover].income)} r={4} fill="var(--income)" stroke="var(--card)" strokeWidth={2} />
            <circle cx={hoverX} cy={yFor(values[hover].expenses)} r={4} fill="var(--expense)" stroke="var(--card)" strokeWidth={2} />
          </>
        )}
      </svg>

      {hoverPoint && (
        <div
          className="pointer-events-none absolute top-0 rounded-md border border-border bg-popover px-3 py-2 text-xs shadow-lg"
          style={{ left: `${(hoverX / WIDTH) * 100}%`, transform: "translate(-50%, -110%)" }}
        >
          <p className="mb-1 font-medium text-popover-foreground">{formatMonth(hoverPoint.month)}</p>
          <p className="text-muted-foreground">
            Income <span className="font-mono-figures text-popover-foreground">{formatCurrencyCompact(hoverPoint.income)}</span>
          </p>
          <p className="text-muted-foreground">
            Expenses <span className="font-mono-figures text-popover-foreground">{formatCurrencyCompact(hoverPoint.expenses)}</span>
          </p>
        </div>
      )}
    </div>
  );
}
