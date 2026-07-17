import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, HeartPulse, Moon, Salad, ShieldAlert, Sparkles, Zap } from "lucide-react";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { ContributionBars } from "../components/ContributionBars";
import { EmptyState } from "../components/EmptyState";
import { LoadingProgress } from "../components/LoadingProgress";
import { PageHeader } from "../components/PageHeader";
import { SeverityBadge } from "../components/SeverityBadge";
import { SourceList } from "../components/SourceList";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { CheckIn, Recommendation } from "../types";
import { formatDate } from "../utils/format";

type CheckInForm = Omit<CheckIn, "id" | "user_id" | "created_at">;

const initial: CheckInForm = {
  sleep_hours: 6,
  sleep_quality: 6,
  energy_level: 5,
  stress_level: 5,
  muscle_soreness: 4,
  pain_or_discomfort: "",
  planned_activity: "",
  notes: ""
};

const levelLabel = {
  high: "высокая",
  moderate: "средняя",
  low: "низкая"
} as const;

function Slider({
  label,
  value,
  onChange
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="rounded-lg border border-line bg-white/65 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="text-base font-extrabold text-ink">{label}</span>
        <span className="rounded-full bg-mint px-3 py-1 text-base font-black text-spruce">{value}/10</span>
      </div>
      <input
        className="h-6 w-full accent-teal"
        type="range"
        min={1}
        max={10}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function ResultSection({ recommendation }: { recommendation: Recommendation }) {
  const result = recommendation.structured_result;
  const insight = result.heart_rate_insight;

  const blocks = [
    { icon: Activity, title: "Движение", block: result.movement },
    { icon: Zap, title: "Восстановление", block: result.recovery },
    { icon: Moon, title: "Сон", block: result.sleep },
    { icon: Salad, title: "Питание", block: result.nutrition }
  ];

  return (
    <div className="space-y-5">
      <div className="card rounded-2xl p-6">
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge value={result.readiness.level} label={`Готовность: ${levelLabel[result.readiness.level]}`} />
          <StatusBadge value={result.movement.intensity} label={`Нагрузка: ${levelLabel[result.movement.intensity]}`} />
          {recommendation.ai_mode === "mock" ? (
            <span className="rounded-full bg-ink/5 px-3 py-1 text-xs font-extrabold text-muted">
              Демо-режим: без языковой модели
            </span>
          ) : null}
        </div>

        <h2 className="mt-5 font-display text-3xl font-semibold text-ink">{result.today_focus}</h2>
        <p className="mt-3 text-lg leading-8 text-muted">{result.summary}</p>

        <div className="mt-4 rounded-xl bg-mint/40 p-4">
          <p className="text-sm font-extrabold uppercase tracking-wide text-spruce">Почему такой вывод</p>
          <p className="mt-1 text-base leading-7 text-ink">{result.readiness.explanation}</p>
        </div>

        {result.medical_safety_message ? (
          <p className="mt-4 rounded-xl bg-amber/10 p-4 text-base font-bold leading-7 text-amber">
            {result.medical_safety_message}
          </p>
        ) : null}
      </div>

      {insight ? (
        <div className="card rounded-2xl p-6">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <HeartPulse className="h-5 w-5 text-teal" aria-hidden="true" />
              <h3 className="text-xl font-black text-ink">Что показал пульс</h3>
            </div>
            <SeverityBadge severity={insight.severity} />
          </div>
          {insight.contributions.length ? <ContributionBars contributions={insight.contributions} /> : null}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        {blocks.map(({ icon: Icon, title, block }) => (
          <article key={title} className="card rounded-2xl p-5">
            <Icon className="mb-3 h-6 w-6 text-teal" aria-hidden="true" />
            <h3 className="text-lg font-black text-ink">{title}</h3>
            <p className="mt-2 text-base leading-7 text-muted">{block.recommendation}</p>
            <p className="mt-3 text-sm font-bold leading-6 text-muted">{block.reasoning}</p>
            <SourceList sources={block.sources} compact />
          </article>
        ))}
      </div>

      <div className="card rounded-2xl p-5">
        <h3 className="mb-3 text-lg font-black text-ink">Чего сегодня лучше избегать</h3>
        <div className="flex flex-wrap gap-2">
          {result.things_to_avoid.map((item) => (
            <span key={item} className="rounded-full bg-amber/10 px-3 py-2 text-sm font-bold text-amber">
              {item}
            </span>
          ))}
        </div>

        <h3 className="mb-3 mt-5 text-lg font-black text-ink">Важно помнить</h3>
        <ul className="space-y-2 text-base leading-7 text-muted">
          {result.important_notes.map((item) => (
            <li key={item}>• {item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export function RecommendationsPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<CheckInForm>(initial);
  const [latest, setLatest] = useState<Recommendation | null>(null);

  const recommendations = useQuery({ queryKey: ["recommendations"], queryFn: api.listRecommendations });

  const generate = useMutation({
    mutationFn: async () => {
      const checkin = await api.createCheckIn(form);
      return api.createRecommendation(checkin.id);
    },
    onSuccess: (data) => {
      setLatest(data);
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      toast.success("План готов");
    },
    onError: (error: Error) => toast.error(error.message)
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    generate.mutate();
  }

  const active = latest ?? recommendations.data?.[0] ?? null;

  return (
    <section>
      <PageHeader title="План дня" eyebrow="Сегодняшнее состояние" />

      <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <form onSubmit={submit} className="card rounded-2xl p-6">
          <h2 className="text-xl font-black text-ink">Как вы сегодня?</h2>
          <div className="mt-5 grid gap-4">
            <label>
              <span className="field-label">Сон, часов</span>
              <input
                className="field text-lg"
                type="number"
                step="0.5"
                min={0}
                max={16}
                value={form.sleep_hours}
                onChange={(event) => setForm({ ...form, sleep_hours: Number(event.target.value) })}
              />
            </label>
            <Slider label="Качество сна" value={form.sleep_quality} onChange={(v) => setForm({ ...form, sleep_quality: v })} />
            <Slider label="Энергия" value={form.energy_level} onChange={(v) => setForm({ ...form, energy_level: v })} />
            <Slider label="Стресс" value={form.stress_level} onChange={(v) => setForm({ ...form, stress_level: v })} />
            <Slider label="Усталость мышц" value={form.muscle_soreness} onChange={(v) => setForm({ ...form, muscle_soreness: v })} />
            <label>
              <span className="field-label">Боль или дискомфорт</span>
              <input
                className="field text-lg"
                value={form.pain_or_discomfort ?? ""}
                onChange={(event) => setForm({ ...form, pain_or_discomfort: event.target.value })}
              />
            </label>
            <label>
              <span className="field-label">Планируемая активность</span>
              <input
                className="field text-lg"
                value={form.planned_activity ?? ""}
                onChange={(event) => setForm({ ...form, planned_activity: event.target.value })}
              />
            </label>
            <label>
              <span className="field-label">Заметки</span>
              <textarea
                className="field min-h-24 text-lg"
                value={form.notes ?? ""}
                onChange={(event) => setForm({ ...form, notes: event.target.value })}
              />
            </label>
          </div>
          <button className="btn btn-primary mt-5 w-full text-lg" type="submit" disabled={generate.isPending}>
            <Sparkles className="h-5 w-5" aria-hidden="true" />
            Создать план на сегодня
          </button>
        </form>

        <div className="space-y-5">
          {generate.isPending ? (
            <LoadingProgress
              steps={["Смотрим профиль", "Учитываем пульс", "Ищем рекомендации в источниках", "Готовим план"]}
            />
          ) : active ? (
            <ResultSection recommendation={active} />
          ) : (
            <EmptyState icon={ShieldAlert} title="План еще не создан" text="Заполните форму слева." />
          )}

          <div className="card rounded-2xl p-5">
            <h3 className="mb-4 text-lg font-black text-ink">История</h3>
            <div className="space-y-3">
              {recommendations.data?.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setLatest(item)}
                  className="w-full rounded-lg border border-line bg-white/65 p-4 text-left hover:border-teal"
                >
                  <p className="font-extrabold text-ink">{item.structured_result.today_focus}</p>
                  <p className="text-sm text-muted">{formatDate(item.created_at)}</p>
                </button>
              ))}
              {!recommendations.data?.length ? (
                <p className="text-base text-muted">История появится после первого плана.</p>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
