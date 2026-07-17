import type { FeatureContribution } from "../types";

/**
 * The explainability surface: which measurements drove the score, and by how
 * much. Bars are labelled with the percentage in text as well, so the ranking
 * survives on a small screen and for a user who cannot judge bar lengths.
 */
export function ContributionBars({
  contributions,
  limit = 3
}: {
  contributions: FeatureContribution[];
  limit?: number;
}) {
  const shown = contributions.slice(0, limit);
  if (!shown.length) return null;

  return (
    <ul className="space-y-4">
      {shown.map((item) => (
        <li key={item.feature}>
          <div className="mb-1.5 flex items-baseline justify-between gap-3">
            <span className="text-base font-extrabold text-ink">{item.label}</span>
            <span className="shrink-0 text-sm font-extrabold text-muted">
              вклад {Math.round(item.weight * 100)}%
            </span>
          </div>
          <div className="h-2.5 overflow-hidden rounded-full bg-line">
            <div
              className={`h-full rounded-full ${
                item.direction === "normal" ? "bg-teal" : "bg-amber"
              }`}
              style={{ width: `${Math.max(4, Math.round(item.weight * 100))}%` }}
            />
          </div>
          <p className="mt-1.5 text-sm leading-6 text-muted">{item.explanation}</p>
        </li>
      ))}
    </ul>
  );
}
