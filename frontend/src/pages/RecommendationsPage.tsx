import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, Moon, Salad, ShieldAlert, Sparkles, Zap } from "lucide-react";
import { FormEvent, useState } from "react";
import { toast } from "sonner";

import { EmptyState } from "../components/EmptyState";
import { LoadingProgress } from "../components/LoadingProgress";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { CheckIn, RecommendationResult } from "../types";
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

function Slider({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="rounded-lg border border-line bg-white/65 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="font-extrabold text-ink">{label}</span>
        <span className="rounded-full bg-mint px-3 py-1 text-sm font-black text-spruce">{value}/10</span>
      </div>
      <input className="w-full accent-teal" type="range" min={1} max={10} value={value} onChange={(e) => onChange(Number(e.target.value))} />
    </label>
  );
}

function ResultSection({ result }: { result: RecommendationResult }) {
  const blocks = [
    { icon: Activity, title: "Движение", text: result.movement.recommendation, note: result.movement.reasoning },
    { icon: Zap, title: "Восстановление", text: result.recovery.recommendation, note: result.recovery.reasoning },
    { icon: Moon, title: "Сон", text: result.sleep.recommendation, note: result.sleep.reasoning },
    { icon: Salad, title: "Питание", text: result.nutrition.recommendation, note: result.nutrition.reasoning }
  ];
  return (
    <div className="space-y-5">
      <div className="card rounded-lg p-6">
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge value={result.readiness.level} label={`Готовность: ${levelLabel[result.readiness.level]}`} />
          <StatusBadge value={result.movement.intensity} label={`Нагрузка: ${levelLabel[result.movement.intensity]}`} />
        </div>
        <h2 className="mt-5 font-display text-3xl font-semibold text-ink">{result.today_focus}</h2>
        <p className="mt-3 text-base leading-7 text-muted">{result.summary}</p>
        {result.medical_safety_message ? <p className="mt-4 rounded-lg bg-amber/10 p-4 text-sm font-bold leading-6 text-amber">{result.medical_safety_message}</p> : null}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {blocks.map(({ icon: Icon, title, text, note }) => (
          <article key={title} className="card rounded-lg p-5">
            <Icon className="mb-4 h-6 w-6 text-teal" />
            <h3 className="text-lg font-black text-ink">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-muted">{text}</p>
            <p className="mt-3 text-xs font-bold leading-5 text-muted">{note}</p>
          </article>
        ))}
      </div>
      <div className="card rounded-lg p-5">
        <h3 className="mb-3 text-lg font-black text-ink">Чего сегодня лучше избегать</h3>
        <div className="flex flex-wrap gap-2">
          {result.things_to_avoid.map((item) => <span key={item} className="rounded-full bg-amber/10 px-3 py-2 text-sm font-bold text-amber">{item}</span>)}
        </div>
      </div>
    </div>
  );
}

export function RecommendationsPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<CheckInForm>(initial);
  const recommendations = useQuery({ queryKey: ["recommendations"], queryFn: api.listRecommendations });
  const [latestResult, setLatestResult] = useState<RecommendationResult | null>(null);

  const generate = useMutation({
    mutationFn: async () => {
      const checkin = await api.createCheckIn(form);
      return api.createRecommendation(checkin.id);
    },
    onSuccess: (data) => {
      setLatestResult(data.structured_result);
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      toast.success("План готов");
    },
    onError: (error) => toast.error(error.message)
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    generate.mutate();
  }

  const activeResult = latestResult ?? recommendations.data?.[0]?.structured_result ?? null;

  return (
    <section>
      <PageHeader title="План дня" eyebrow="Сегодняшнее состояние" />
      <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <form onSubmit={submit} className="card rounded-lg p-6">
          <h2 className="text-xl font-black text-ink">Как вы сегодня?</h2>
          <div className="mt-5 grid gap-4">
            <label><span className="field-label">Сон, часов</span><input className="field" type="number" step="0.5" value={form.sleep_hours} onChange={(e) => setForm({ ...form, sleep_hours: Number(e.target.value) })} /></label>
            <Slider label="Качество сна" value={form.sleep_quality} onChange={(value) => setForm({ ...form, sleep_quality: value })} />
            <Slider label="Энергия" value={form.energy_level} onChange={(value) => setForm({ ...form, energy_level: value })} />
            <Slider label="Стресс" value={form.stress_level} onChange={(value) => setForm({ ...form, stress_level: value })} />
            <Slider label="Усталость мышц" value={form.muscle_soreness} onChange={(value) => setForm({ ...form, muscle_soreness: value })} />
            <label><span className="field-label">Боль или дискомфорт</span><input className="field" value={form.pain_or_discomfort ?? ""} onChange={(e) => setForm({ ...form, pain_or_discomfort: e.target.value })} /></label>
            <label><span className="field-label">Планируемая активность</span><input className="field" value={form.planned_activity ?? ""} onChange={(e) => setForm({ ...form, planned_activity: e.target.value })} /></label>
            <label><span className="field-label">Заметки</span><textarea className="field min-h-24" value={form.notes ?? ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
          </div>
          <button className="btn btn-primary mt-5 w-full" type="submit" disabled={generate.isPending}>
            <Sparkles className="h-5 w-5" />
            Создать мой план на сегодня
          </button>
        </form>

        <div className="space-y-5">
          {generate.isPending ? (
            <LoadingProgress steps={["Смотрим профиль", "Учитываем состояние", "Готовим план"]} />
          ) : activeResult ? (
            <ResultSection result={activeResult} />
          ) : (
            <EmptyState icon={ShieldAlert} title="План еще не создан" text="Заполните форму слева." />
          )}
          <div className="card rounded-lg p-5">
            <h3 className="mb-4 text-lg font-black text-ink">История</h3>
            <div className="space-y-3">
              {recommendations.data?.map((item) => (
                <div key={item.id} className="rounded-lg border border-line bg-white/65 p-4">
                  <p className="font-extrabold text-ink">{item.structured_result.today_focus}</p>
                  <p className="text-sm text-muted">{formatDate(item.created_at)}</p>
                </div>
              ))}
              {!recommendations.data?.length ? <p className="text-sm text-muted">История появится после первого плана.</p> : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
