import { useQuery } from "@tanstack/react-query";
import { Activity, CalendarDays, FileText, ShieldCheck, UserRound } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { LiveHeartRate } from "../components/LiveHeartRate";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";
import { completionPercent, formatDate, formatTime } from "../utils/format";

const readinessLabel = {
  high: "Высокая",
  moderate: "Средняя",
  low: "Низкая"
} as const;

function greeting(name: string) {
  const hour = new Date().getHours();
  const part =
    hour < 6 ? "Доброй ночи" : hour < 12 ? "Доброе утро" : hour < 18 ? "Добрый день" : "Добрый вечер";
  return name ? `${part}, ${name}` : part;
}

export function DashboardPage() {
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.getProfile });
  const recommendations = useQuery({ queryKey: ["recommendations"], queryFn: api.listRecommendations });
  const documents = useQuery({ queryKey: ["documents"], queryFn: api.listDocumentAnalyses });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.listIncidents });

  const latest = recommendations.data?.[0];
  const completion = completionPercent(profile.data);

  return (
    <section>
      <PageHeader title={greeting(profile.data?.name ?? "")} eyebrow="Ваш обзор здоровья">
        <div className="inline-flex min-h-12 items-center gap-2 rounded-full bg-white px-4 text-base font-extrabold text-muted shadow-insetline">
          <CalendarDays className="h-5 w-5 text-teal" aria-hidden="true" />
          {formatDate()}
        </div>
      </PageHeader>

      <div className="grid gap-5 xl:grid-cols-2">
        <LiveHeartRate compact />

        <article className="card overflow-hidden rounded-2xl">
          <div className="p-6 md:p-7">
            <h2 className="font-display text-3xl font-semibold text-ink">Ваш фокус на сегодня</h2>
            <p className="mt-3 text-lg leading-8 text-muted">
              {latest?.structured_result.summary ?? "Заполните короткую форму и получите план на день."}
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <Link to="/recommendations" className="btn btn-primary text-base">
                <Activity className="h-5 w-5" aria-hidden="true" />
                Получить план
              </Link>
              <Link to="/documents" className="btn btn-secondary text-base">
                <FileText className="h-5 w-5" aria-hidden="true" />
                Разобрать анализы
              </Link>
            </div>
          </div>
          <div className="border-t border-line bg-spruce p-6 text-white">
            <p className="text-sm font-extrabold uppercase tracking-wide text-white/65">Готовность</p>
            <p className="mt-2 text-4xl font-black">
              {latest ? readinessLabel[latest.structured_result.readiness.level] : "—"}
            </p>
            <p className="mt-3 text-base leading-7 text-white/75">
              {latest?.structured_result.readiness.explanation ?? "Появится после первого плана."}
            </p>
          </div>
        </article>
      </div>

      <div className="mt-5 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        <Link to="/heart-rate" className="card rounded-2xl p-5 transition hover:-translate-y-1">
          <MetricCard icon={Activity} label="Пульс" value="Наблюдение" detail="Оценка ритма и объяснение" />
        </Link>
        <Link to="/documents" className="card rounded-2xl p-5 transition hover:-translate-y-1">
          <MetricCard icon={FileText} label="Анализы" value="Разбор PDF" detail="Питание и активность" />
        </Link>
        <Link to="/safety" className="card rounded-2xl p-5 transition hover:-translate-y-1">
          <MetricCard icon={ShieldCheck} label="Безопасность" value="Падения" detail="Контакты и Telegram" />
        </Link>
        <Link to="/profile" className="card rounded-2xl p-5 transition hover:-translate-y-1">
          <MetricCard icon={UserRound} label="Профиль" value={`${completion}%`} detail="Заполните для точного плана" />
        </Link>
      </div>

      <section className="mt-5 grid gap-5 lg:grid-cols-3">
        <div className="card rounded-2xl p-5">
          <h3 className="mb-4 text-lg font-black text-ink">Последняя рекомендация</h3>
          {latest ? (
            <p className="text-base leading-7 text-muted">{latest.structured_result.today_focus}</p>
          ) : (
            <EmptyState icon={Activity} title="Плана пока нет" text="Заполните форму состояния." />
          )}
        </div>
        <div className="card rounded-2xl p-5">
          <h3 className="mb-4 text-lg font-black text-ink">Последний разбор анализов</h3>
          {documents.data?.[0] ? (
            <p className="text-base leading-7 text-muted">
              {documents.data[0].original_filename} · {formatDate(documents.data[0].created_at)}
            </p>
          ) : (
            <EmptyState icon={FileText} title="История пуста" text="Загрузите PDF с результатами." />
          )}
        </div>
        <div className="card rounded-2xl p-5">
          <h3 className="mb-4 text-lg font-black text-ink">Последний инцидент</h3>
          {incidents.data?.[0] ? (
            <p className="text-base leading-7 text-muted">
              Возможное падение · {formatTime(incidents.data[0].event_timestamp)}
            </p>
          ) : (
            <EmptyState
              icon={ShieldCheck}
              title="Инцидентов нет"
              text="Проверку можно запустить на странице «Безопасность»."
            />
          )}
        </div>
      </section>
    </section>
  );
}
