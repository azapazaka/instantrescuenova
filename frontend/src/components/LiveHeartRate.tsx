import { useQuery } from "@tanstack/react-query";
import { Heart } from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../services/api";
import type { HeartRateLive } from "../types";
import { cn } from "../utils/style";
import { HeartRateSparkline } from "./HeartRateSparkline";
import { SeverityBadge } from "./SeverityBadge";

const zoneTone: Record<HeartRateLive["zone"], string> = {
  low: "text-ai",
  normal: "text-spruce",
  elevated: "text-amber",
  high: "text-emergency",
  unknown: "text-muted"
};

export const LIVE_POLL_MS = 5000;

export function LiveHeartRate({ compact = false }: { compact?: boolean }) {
  const live = useQuery({
    queryKey: ["hr-live"],
    queryFn: api.liveHeartRate,
    refetchInterval: LIVE_POLL_MS
  });

  const history = useQuery({
    queryKey: ["hr-history", 1],
    queryFn: () => api.heartRateHistory(1),
    refetchInterval: LIVE_POLL_MS
  });

  const data = live.data;
  const anomaly = data?.latest_anomaly;
  const simulated = data?.source === "simulated";

  return (
    <article className="card rounded-2xl p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-extrabold uppercase tracking-wide text-teal">Пульс сейчас</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={cn("text-6xl font-black tabular-nums", zoneTone[data?.zone ?? "unknown"])}>
              {data?.bpm ? Math.round(data.bpm) : "—"}
            </span>
            {/* nowrap: at 375px the badge squeezes this and "уд/мин" breaks mid-unit. */}
            <span className="whitespace-nowrap text-xl font-extrabold text-muted">уд/мин</span>
          </div>
          <p className="mt-1 text-base font-extrabold text-muted">{data?.zone_label ?? "Нет данных"}</p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div
            className={cn(
              "flex h-12 w-12 items-center justify-center rounded-xl bg-mint",
              zoneTone[data?.zone ?? "unknown"]
            )}
          >
            {/* Pulse animation is decorative; aria-hidden keeps it out of the a11y tree. */}
            <Heart className="h-6 w-6 animate-pulse" aria-hidden="true" />
          </div>
          {anomaly ? <SeverityBadge severity={anomaly.severity} /> : null}
        </div>
      </div>

      <div className="mt-5">
        <HeartRateSparkline readings={history.data ?? []} height={compact ? 48 : 64} />
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-line pt-4">
        <div>
          <dt className="text-sm font-bold text-muted">Пульс покоя</dt>
          <dd className="text-lg font-extrabold text-ink">
            {data?.resting_baseline ? `${Math.round(data.resting_baseline)} уд/мин` : "Собираем данные"}
          </dd>
        </div>
        <div>
          <dt className="text-sm font-bold text-muted">Источник</dt>
          <dd className="text-lg font-extrabold text-ink">{simulated ? "Симуляция" : "Датчик"}</dd>
        </div>
      </dl>

      {anomaly?.rate_flag ? (
        <p className="mt-4 rounded-lg bg-amber/10 p-3 text-sm font-semibold leading-6 text-amber">
          {anomaly.rate_flag}. Это не диагноз — обсудите показатели с врачом.
        </p>
      ) : null}

      {simulated ? (
        <p className="mt-4 text-xs leading-5 text-muted">
          Демо-режим: данные пульса смоделированы. Реальный датчик подключается без
          изменений в приложении.
        </p>
      ) : null}

      {!compact ? null : (
        <Link to="/heart-rate" className="btn btn-secondary mt-4 w-full">
          Подробнее о пульсе
        </Link>
      )}
    </article>
  );
}
