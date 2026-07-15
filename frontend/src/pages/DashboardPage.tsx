import { useQuery } from "@tanstack/react-query";
import { Activity, CalendarDays, FileText, ShieldCheck, UserRound } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/EmptyState";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";
import { completionPercent, formatDate, formatTime } from "../utils/format";

const readinessLabel = {
  high: "Высокая",
  moderate: "Средняя",
  low: "Низкая"
} as const;

export function DashboardPage() {
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.getProfile });
  const recommendations = useQuery({ queryKey: ["recommendations"], queryFn: api.listRecommendations });
  const ecg = useQuery({ queryKey: ["ecg"], queryFn: api.listECGAnalyses });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.listIncidents });

  const latestRecommendation = recommendations.data?.[0];
  const completion = completionPercent(profile.data);

  return (
    <section>
      <PageHeader title={`Доброе утро, ${profile.data?.name ?? "Азамат"}`} eyebrow="Ваш персональный обзор здоровья">
        <div className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-extrabold text-muted shadow-insetline">
          <CalendarDays className="h-4 w-4 text-teal" />
          {formatDate()}
        </div>
      </PageHeader>

      <div className="grid gap-5 xl:grid-cols-[1.45fr_0.9fr]">
        <article className="card overflow-hidden rounded-lg">
          <div className="grid gap-0 md:grid-cols-[1fr_230px]">
            <div className="p-6 md:p-8">
              <h2 className="font-display text-4xl font-semibold text-ink">Ваш фокус на сегодня</h2>
              <p className="mt-4 max-w-2xl text-lg leading-8 text-muted">
                {latestRecommendation?.structured_result.summary ??
                  "Заполните короткую форму и получите план на день."}
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link to="/recommendations" className="btn btn-primary">
                  <Activity className="h-5 w-5" />
                  Получить рекомендации
                </Link>
                <Link to="/ecg" className="btn btn-secondary">
                  <FileText className="h-5 w-5" />
                  Проанализировать ЭКГ
                </Link>
              </div>
            </div>
            <div className="border-t border-line bg-spruce p-6 text-white md:border-l md:border-t-0">
              <p className="text-sm font-extrabold uppercase tracking-wide text-white/65">Готовность</p>
              <p className="mt-4 text-5xl font-black">
                {latestRecommendation
                  ? readinessLabel[latestRecommendation.structured_result.readiness.level]
                  : "Средняя"}
              </p>
              <p className="mt-4 text-sm leading-6 text-white/70">
                {latestRecommendation?.structured_result.readiness.explanation ??
                  "Появится после первого плана."}
              </p>
            </div>
          </div>
        </article>

        <article className="card rounded-lg p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-extrabold uppercase tracking-wide text-teal">Профиль</p>
              <h2 className="mt-2 text-3xl font-black text-ink">{completion}%</h2>
            </div>
            <UserRound className="h-9 w-9 text-teal" />
          </div>
          <div className="mt-5 h-3 overflow-hidden rounded-full bg-line">
            <div className="h-full rounded-full bg-teal" style={{ width: `${completion}%` }} />
          </div>
          <p className="mt-4 text-sm leading-6 text-muted">Заполните основные данные для точного плана.</p>
          <Link to="/profile" className="btn btn-secondary mt-5 w-full">
            Завершить профиль
          </Link>
        </article>
      </div>

      <div className="mt-5 grid gap-5 md:grid-cols-3">
        <Link to="/recommendations" className="card rounded-lg p-5 hover:-translate-y-1 transition">
          <MetricCard icon={Activity} label="Рекомендации" value="План дня" detail="Нагрузка, сон, восстановление" />
        </Link>
        <Link to="/ecg" className="card rounded-lg p-5 hover:-translate-y-1 transition">
          <MetricCard icon={FileText} label="ЭКГ" value="Разбор PDF" detail="Показатели и вопросы врачу" />
        </Link>
        <Link to="/safety" className="card rounded-lg p-5 hover:-translate-y-1 transition">
          <MetricCard icon={ShieldCheck} label="Безопасность" value="Проверка падения" detail="Контакты и уведомления" />
        </Link>
      </div>

      <section className="mt-5 grid gap-5 lg:grid-cols-3">
        <div className="card rounded-lg p-5">
          <h3 className="mb-4 text-lg font-black text-ink">Последняя рекомендация</h3>
          {latestRecommendation ? (
            <p className="text-sm leading-6 text-muted">{latestRecommendation.structured_result.today_focus}</p>
          ) : (
            <EmptyState icon={Activity} title="Плана пока нет" text="Заполните форму состояния." />
          )}
        </div>
        <div className="card rounded-lg p-5">
          <h3 className="mb-4 text-lg font-black text-ink">Последний анализ ЭКГ</h3>
          {ecg.data?.[0] ? (
            <p className="text-sm leading-6 text-muted">{ecg.data[0].original_filename} · {formatDate(ecg.data[0].created_at)}</p>
          ) : (
            <EmptyState icon={FileText} title="История пуста" text="Загрузите PDF с результатами ЭКГ." />
          )}
        </div>
        <div className="card rounded-lg p-5">
          <h3 className="mb-4 text-lg font-black text-ink">Последний инцидент</h3>
          {incidents.data?.[0] ? (
            <p className="text-sm leading-6 text-muted">Возможное падение · {formatTime(incidents.data[0].event_timestamp)}</p>
          ) : (
            <EmptyState icon={ShieldCheck} title="Инцидентов нет" text="Проверку можно запустить на странице безопасности." />
          )}
        </div>
      </section>
    </section>
  );
}
