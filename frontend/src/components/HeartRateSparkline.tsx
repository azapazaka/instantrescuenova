import type { HeartRateReading } from "../types";

/**
 * Inline SVG sparkline. No chart library: this draws one polyline, and pulling
 * in a charting dependency for it would cost more bundle than the whole page.
 */
export function HeartRateSparkline({
  readings,
  height = 64
}: {
  readings: HeartRateReading[];
  height?: number;
}) {
  if (readings.length < 2) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-dashed border-line text-sm text-muted"
        style={{ height }}
      >
        Собираем данные…
      </div>
    );
  }

  const values = readings.map((r) => r.bpm);
  const min = Math.min(...values);
  const max = Math.max(...values);
  // Guard against a flat series collapsing the range to zero and dividing by 0.
  const range = max - min || 1;
  const width = 100;

  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 8) - 4;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="w-full"
      style={{ height }}
      role="img"
      aria-label={`График пульса: от ${Math.round(min)} до ${Math.round(max)} ударов в минуту`}
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
        className="text-teal"
      />
    </svg>
  );
}
