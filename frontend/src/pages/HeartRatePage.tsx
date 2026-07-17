import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, BrainCircuit, HeartPulse, Info } from "lucide-react";
import { toast } from "sonner";

import { ContributionBars } from "../components/ContributionBars";
import { EmptyState } from "../components/EmptyState";
import { HeartRateSparkline } from "../components/HeartRateSparkline";
import { LiveHeartRate } from "../components/LiveHeartRate";
import { PageHeader } from "../components/PageHeader";
import { SeverityBadge } from "../components/SeverityBadge";
import { api } from "../services/api";
import { formatTime } from "../utils/format";

export function HeartRatePage() {
  const queryClient = useQueryClient();

  const summary = useQuery({ queryKey: ["hr-summary"], queryFn: () => api.heartRateSummary(24) });
  const history = useQuery({ queryKey: ["hr-history", 6], queryFn: () => api.heartRateHistory(6) });
  const anomalies = useQuery({ queryKey: ["hr-anomalies"], queryFn: () => api.heartRateAnomalies(10) });
  const scenario = useQuery({ queryKey: ["hr-scenario"], queryFn: api.getScenario });

  const setScenario = useMutation({
    mutationFn: api.setScenario,
    onSuccess: (data) => {
      toast.success(`Сценарий: ${data.available[data.scenario]}`);
      // The scenario switch rewrites the current window and rescores it, so
      // every heart-rate view is stale — not just the scenario itself.
      for (const key of ["hr-scenario", "hr-anomalies", "hr-live", "hr-history", "hr-summary"]) {
        queryClient.invalidateQueries({ queryKey: [key] });
      }
    },
    onError: (error: Error) => toast.error(error.message)
  });

  const latest = anomalies.data?.[0];
  const simulated = scenario.data?.source === "simulated";

  return (
    <section>
      <PageHeader title="Пульс" eyebrow="Наблюдение в реальном времени" />

      <div className="grid gap-5 lg:grid-cols-[1fr_1.1fr]">
        <LiveHeartRate />

        <article className="card rounded-2xl p-6">
          <div className="mb-4 flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-ai" aria-hidden="true" />
            <h2 className="text-xl font-black text-ink">Что увидела модель</h2>
          </div>

          {latest ? (
            <>
              <div className="mb-4 flex flex-wrap items-center gap-3">
                <SeverityBadge severity={latest.severity} />
                <span className="text-sm font-bold text-muted">
                  окно {formatTime(latest.window_start)}–{formatTime(latest.window_end)}
                </span>
              </div>

              <ContributionBars contributions={latest.contributions} limit={3} />

              <div className="mt-5 space-y-2 border-t border-line pt-4 text-sm leading-6 text-muted">
                <p className="flex gap-2">
                  <Info className="mt-0.5 h-4 w-4 shrink-0 text-ai" aria-hidden="true" />
                  <span>
                    Сравнение идёт с{" "}
                    <strong className="text-ink">
                      {latest.baseline_source === "personal"
                        ? "вашей личной нормой"
                        : "нормой здорового взрослого"}
                    </strong>
                    {latest.baseline_source === "personal"
                      ? "."
                      : ". Когда накопится ваша история, сравнение станет персональным."}
                  </span>
                </p>
                <p>
                  Модель может ошибаться: она видит только пульс и не знает о лекарствах,
                  температуре и эмоциях. Итоговое решение всегда за вами и вашим врачом.
                </p>
              </div>
            </>
          ) : (
            <EmptyState
              icon={BrainCircuit}
              title="Данных пока мало"
              text="Модель оценивает пульс окнами по 5 минут. Оценка появится, как только наберётся достаточно измерений."
            />
          )}
        </article>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <article className="card rounded-2xl p-6 lg:col-span-2">
          <h2 className="mb-4 text-xl font-black text-ink">За последние 6 часов</h2>
          <div className="text-teal">
            <HeartRateSparkline readings={history.data ?? []} height={120} />
          </div>
          <dl className="mt-5 grid grid-cols-2 gap-4 border-t border-line pt-4 sm:grid-cols-4">
            {[
              ["Средний", summary.data?.average_bpm],
              ["Минимум", summary.data?.min_bpm],
              ["Максимум", summary.data?.max_bpm],
              ["Покой", summary.data?.resting_bpm]
            ].map(([label, value]) => (
              <div key={String(label)}>
                <dt className="text-sm font-bold text-muted">{label}</dt>
                <dd className="text-2xl font-black tabular-nums text-ink">
                  {value ? Math.round(Number(value)) : "—"}
                </dd>
              </div>
            ))}
          </dl>
          <p className="mt-3 text-sm text-muted">
            {summary.data?.reading_count ?? 0} измерений за 24 часа.
          </p>
        </article>

        {simulated ? (
          <article className="card rounded-2xl p-6">
            <div className="mb-3 flex items-center gap-2">
              <Activity className="h-5 w-5 text-ai" aria-hidden="true" />
              <h2 className="text-xl font-black text-ink">Демо-сценарии</h2>
            </div>
            <p className="mb-4 text-sm leading-6 text-muted">
              Переключите ритм, чтобы увидеть, как модель реагирует. Только для
              демонстрации — это не измерение вашего сердца.
            </p>
            <div className="space-y-2">
              {Object.entries(scenario.data?.available ?? {}).map(([key, label]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setScenario.mutate(key)}
                  disabled={setScenario.isPending}
                  className={`w-full rounded-lg border px-4 py-3 text-left text-sm font-extrabold transition ${
                    scenario.data?.scenario === key
                      ? "border-spruce bg-spruce text-white"
                      : "border-line bg-white text-ink hover:bg-ink/5"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </article>
        ) : null}
      </div>

      <article className="card mt-5 rounded-2xl p-6">
        <h2 className="mb-4 text-xl font-black text-ink">История оценок</h2>
        {anomalies.data?.length ? (
          <ul className="space-y-3">
            {anomalies.data.map((item) => (
              <li
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-line bg-white/60 p-4"
              >
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={item.severity} />
                  <span className="text-sm font-bold text-muted">
                    {formatTime(item.window_start)}–{formatTime(item.window_end)}
                  </span>
                </div>
                <span className="text-sm font-semibold text-muted">
                  {item.contributions[0]?.label}: {item.contributions[0]?.value}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState icon={HeartPulse} title="Оценок пока нет" text="Они появятся по мере накопления измерений." />
        )}
      </article>
    </section>
  );
}
