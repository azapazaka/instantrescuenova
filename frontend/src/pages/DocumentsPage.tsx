import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Apple, Dumbbell, FileText, TriangleAlert, Upload, X } from "lucide-react";
import { useState, type ChangeEvent } from "react";
import { toast } from "sonner";

import { EmptyState } from "../components/EmptyState";
import { LoadingProgress } from "../components/LoadingProgress";
import { PageHeader } from "../components/PageHeader";
import { SourceList } from "../components/SourceList";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { HealthDocument, LifestyleAdvice } from "../types";
import { formatDate } from "../utils/format";

const importanceLabel: Record<string, string> = {
  low: "низкая важность",
  moderate: "средняя важность",
  high: "высокая важность"
};

const measurementTone: Record<string, string> = {
  normal: "bg-mint text-spruce",
  borderline: "bg-amber/15 text-amber",
  out_of_range: "bg-emergency/10 text-emergency",
  unknown: "bg-ink/5 text-muted"
};

const measurementLabel: Record<string, string> = {
  normal: "в норме",
  borderline: "погранично",
  out_of_range: "вне нормы",
  unknown: "нет нормы"
};

function AdviceCard({
  title,
  icon: Icon,
  items
}: {
  title: string;
  icon: typeof Apple;
  items: LifestyleAdvice[];
}) {
  if (!items?.length) return null;
  return (
    <div className="card rounded-2xl p-6">
      <div className="mb-4 flex items-center gap-2">
        <Icon className="h-5 w-5 text-teal" aria-hidden="true" />
        <h3 className="text-xl font-black text-ink">{title}</h3>
      </div>
      <div className="space-y-5">
        {items.map((item) => (
          <div key={item.recommendation}>
            <p className="text-base font-extrabold leading-7 text-ink">{item.recommendation}</p>
            <p className="mt-1 text-sm leading-6 text-muted">{item.reasoning}</p>
            <SourceList sources={item.sources} compact />
          </div>
        ))}
      </div>
    </div>
  );
}

function DocumentReport({ analysis }: { analysis: HealthDocument }) {
  const result = analysis.structured_result;

  return (
    <article className="space-y-5">
      <div className="card rounded-2xl p-6">
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge
            value={result.analysis_status === "completed" ? "completed" : "waiting"}
            label={result.analysis_status === "completed" ? "Разбор готов" : "Ограниченный разбор"}
          />
          {analysis.ai_mode === "mock" ? (
            <span className="rounded-full bg-ink/5 px-3 py-1 text-xs font-extrabold text-muted">
              Демо-режим: без языковой модели
            </span>
          ) : null}
        </div>
        <h2 className="mt-4 font-display text-3xl font-semibold text-ink">{result.document_type}</h2>
        <p className="mt-3 text-lg leading-8 text-muted">{result.document_summary}</p>
      </div>

      {result.urgent_flags?.length ? (
        <div className="rounded-2xl border-2 border-emergency bg-emergency/5 p-6">
          <div className="flex items-center gap-2">
            <TriangleAlert className="h-6 w-6 text-emergency" aria-hidden="true" />
            <h3 className="text-xl font-black text-emergency">Срочно обратитесь к врачу</h3>
          </div>
          <ul className="mt-3 space-y-2 text-base leading-7 text-ink">
            {result.urgent_flags.map((flag) => (
              <li key={flag}>• {flag}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {result.detected_measurements.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {result.detected_measurements.map((metric) => (
            <div key={metric.name} className="card rounded-2xl p-5">
              <p className="text-sm font-bold text-muted">{metric.name}</p>
              <p className="mt-2 text-2xl font-black text-ink">{metric.value}</p>
              {metric.reference_range ? (
                <p className="mt-1 text-sm text-muted">Норма: {metric.reference_range}</p>
              ) : null}
              <span
                className={`mt-3 inline-block rounded-full px-3 py-1 text-xs font-extrabold ${
                  measurementTone[metric.status] ?? measurementTone.unknown
                }`}
              >
                {measurementLabel[metric.status] ?? metric.status}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        <AdviceCard title="Питание" icon={Apple} items={result.nutrition_advice} />
        <AdviceCard title="Активность" icon={Dumbbell} items={result.activity_advice} />
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        {result.observations.length ? (
          <div className="card rounded-2xl p-6">
            <h3 className="mb-4 text-xl font-black text-ink">Наблюдения</h3>
            {result.observations.map((item) => (
              <div key={item.title} className="mb-3 rounded-lg border border-line bg-white/65 p-4">
                <StatusBadge value={item.importance} label={importanceLabel[item.importance] ?? item.importance} />
                <p className="mt-3 font-extrabold text-ink">{item.title}</p>
                <p className="mt-1 text-base leading-7 text-muted">{item.description}</p>
              </div>
            ))}
          </div>
        ) : null}

        <div className="card rounded-2xl p-6">
          <h3 className="mb-3 text-xl font-black text-ink">Что спросить у врача</h3>
          <ul className="space-y-2 text-base leading-7 text-muted">
            {result.questions_for_doctor.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>

          <h3 className="mb-3 mt-6 text-xl font-black text-ink">Ограничения разбора</h3>
          <ul className="space-y-2 text-base leading-7 text-muted">
            {result.limitations.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
          <p className="mt-4 rounded-lg bg-mint/50 p-3 text-sm leading-6 text-spruce">
            Качество документа: {result.document_quality.explanation}
          </p>
        </div>
      </div>
    </article>
  );
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [selected, setSelected] = useState<HealthDocument | null>(null);

  const history = useQuery({ queryKey: ["documents"], queryFn: api.listDocumentAnalyses });

  const analyze = useMutation({
    mutationFn: api.createDocumentAnalysis,
    onSuccess: (data) => {
      setSelected(data);
      setFile(null);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Разбор готов");
    },
    onError: (error: Error) => toast.error(error.message)
  });

  function pick(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.files?.[0] ?? null;
    if (next && next.type !== "application/pdf") {
      toast.error("Поддерживаются только PDF-файлы");
      return;
    }
    setFile(next);
  }

  const active = selected ?? history.data?.[0] ?? null;

  return (
    <section>
      <PageHeader title="Анализы" eyebrow="Разбор медицинских PDF" />

      <div className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
        <aside className="space-y-5">
          <div className="card rounded-2xl p-6">
            <p className="text-base leading-7 text-muted">
              Загрузите PDF с результатами анализов, дневником давления или заключением по
              пульсу. Мы объясним показатели простым языком и дадим рекомендации по питанию
              и активности со ссылками на источники.
            </p>

            <label className="mt-5 flex min-h-52 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-line bg-white/60 p-6 text-center hover:border-teal">
              <Upload className="mb-3 h-10 w-10 text-teal" aria-hidden="true" />
              <span className="text-lg font-extrabold text-ink">
                {file ? file.name : "Выберите PDF"}
              </span>
              <span className="mt-1 text-sm text-muted">
                {file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : "PDF до 20 MB, до 10 страниц"}
              </span>
              <input className="sr-only" type="file" accept="application/pdf,.pdf" onChange={pick} />
            </label>

            {file ? (
              <button className="btn btn-secondary mt-3 w-full" type="button" onClick={() => setFile(null)}>
                <X className="h-5 w-5" aria-hidden="true" /> Убрать файл
              </button>
            ) : null}

            <button
              className="btn btn-primary mt-3 w-full text-lg"
              disabled={!file || analyze.isPending}
              onClick={() => file && analyze.mutate(file)}
            >
              Начать разбор
            </button>

            <p className="mt-4 text-xs leading-5 text-muted">
              Сам файл не сохраняется — мы храним только результат разбора.
            </p>
          </div>

          <div className="card rounded-2xl p-5">
            <h3 className="mb-4 text-lg font-black text-ink">История разборов</h3>
            <div className="space-y-3">
              {history.data?.map((item) => (
                <button
                  key={item.id}
                  className="w-full rounded-lg border border-line bg-white/65 p-4 text-left hover:border-teal"
                  onClick={() => setSelected(item)}
                >
                  <p className="font-extrabold text-ink">{item.original_filename}</p>
                  <p className="text-sm text-muted">{formatDate(item.created_at)}</p>
                </button>
              ))}
              {!history.data?.length ? (
                <EmptyState icon={FileText} title="История пуста" text="Первый разбор появится после загрузки PDF." />
              ) : null}
            </div>
          </div>
        </aside>

        {analyze.isPending ? (
          <LoadingProgress steps={["Читаем PDF", "Ищем показатели", "Подбираем источники", "Готовим рекомендации"]} />
        ) : active ? (
          <DocumentReport analysis={active} />
        ) : (
          <EmptyState
            icon={FileText}
            title="Загрузите документ"
            text="Появятся показатели, рекомендации по питанию и активности, и вопросы врачу."
          />
        )}
      </div>
    </section>
  );
}
