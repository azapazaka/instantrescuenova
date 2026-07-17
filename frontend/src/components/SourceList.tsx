import { ExternalLink } from "lucide-react";

import type { Source } from "../types";

/**
 * Renders the guideline citations behind a recommendation.
 *
 * Every source here came from the curated corpus, not from the model, so each
 * link resolves to a real WHO/ESC/AHA page the user or their doctor can check.
 */
export function SourceList({ sources, compact = false }: { sources: Source[]; compact?: boolean }) {
  if (!sources?.length) return null;

  return (
    <div className={compact ? "mt-3" : "mt-4"}>
      <p className="mb-2 text-xs font-extrabold uppercase tracking-wide text-muted">Источники</p>
      <ul className="space-y-1.5">
        {sources.map((source) => (
          <li key={source.url + source.title}>
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex items-start gap-1.5 text-sm font-semibold leading-5 text-ai underline underline-offset-2 hover:text-spruce"
            >
              <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <span>
                {source.title}
                <span className="font-normal text-muted">
                  {" "}
                  — {source.org}
                  {source.year ? `, ${source.year}` : ""}
                </span>
              </span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
