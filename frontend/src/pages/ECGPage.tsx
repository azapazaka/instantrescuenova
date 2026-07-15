import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Upload, X } from "lucide-react";
import { ChangeEvent, useState } from "react";
import { toast } from "sonner";

import { EmptyState } from "../components/EmptyState";
import { LoadingProgress } from "../components/LoadingProgress";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import type { ECGAnalysis } from "../types";
import { formatDate } from "../utils/format";

function ECGReport({ analysis }: { analysis: ECGAnalysis }) {
  const result = analysis.structured_result;
  return (
    <article className="space-y-5">
      <div className="card rounded-lg p-6">
        <StatusBadge value={analysis.status} label="Analysis completed" />
        <h2 className="mt-4 font-display text-3xl font-semibold text-ink">Общий обзор</h2>
        <p className="mt-3 leading-7 text-muted">{result.document_summary}</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {result.detected_measurements.map((metric) => (
          <div key={metric.name} className="card rounded-lg p-5">
            <p className="text-sm font-bold text-muted">{metric.name}</p>
            <p className="mt-2 text-lg font-black text-ink">{metric.value}</p>
            <p className="mt-2 text-xs font-bold text-muted">Page {metric.source_page ?? "n/a"}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card rounded-lg p-5">
          <h3 className="mb-3 text-lg font-black text-ink">Наблюдения AI</h3>
          {result.observations.map((item) => (
            <div key={item.title} className="mb-3 rounded-lg border border-line bg-white/65 p-4">
              <StatusBadge value={item.importance} label={item.importance} />
              <p className="mt-3 font-extrabold text-ink">{item.title}</p>
              <p className="mt-1 text-sm leading-6 text-muted">{item.description}</p>
            </div>
          ))}
        </div>
        <div className="card rounded-lg p-5">
          <h3 className="mb-3 text-lg font-black text-ink">Что спросить у врача</h3>
          <ul className="space-y-2 text-sm leading-6 text-muted">
            {result.questions_for_doctor.map((item) => <li key={item}>• {item}</li>)}
          </ul>
          <h3 className="mb-3 mt-5 text-lg font-black text-ink">Ограничения анализа</h3>
          <ul className="space-y-2 text-sm leading-6 text-muted">
            {result.limitations.map((item) => <li key={item}>• {item}</li>)}
          </ul>
        </div>
      </div>
    </article>
  );
}

export function ECGPage() {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [selected, setSelected] = useState<ECGAnalysis | null>(null);
  const history = useQuery({ queryKey: ["ecg"], queryFn: api.listECGAnalyses });

  const analyze = useMutation({
    mutationFn: api.createECGAnalysis,
    onSuccess: (data) => {
      setSelected(data);
      queryClient.invalidateQueries({ queryKey: ["ecg"] });
      toast.success("ECG анализ готов");
    },
    onError: (error) => toast.error(error.message)
  });

  function pick(event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0] ?? null;
    if (nextFile && nextFile.type !== "application/pdf") {
      toast.error("Поддерживаются только PDF-файлы");
      return;
    }
    setFile(nextFile);
  }

  const active = selected ?? history.data?.[0] ?? null;

  return (
    <section>
      <PageHeader title="Анализ ЭКГ" eyebrow="AI-assisted PDF review" />
      <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <aside className="space-y-5">
          <div className="card rounded-lg p-6">
            <p className="text-sm leading-6 text-muted">Загрузите PDF с результатами ЭКГ, чтобы получить понятное AI-assisted объяснение документа.</p>
            <label className="mt-5 flex min-h-52 cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-line bg-white/60 p-6 text-center hover:border-teal">
              <Upload className="mb-3 h-9 w-9 text-teal" />
              <span className="font-extrabold text-ink">{file ? file.name : "Выберите или перетащите PDF"}</span>
              {file ? <span className="mt-1 text-sm text-muted">{(file.size / 1024 / 1024).toFixed(2)} MB</span> : <span className="mt-1 text-sm text-muted">Анализ не начнется автоматически</span>}
              <input className="sr-only" type="file" accept="application/pdf,.pdf" onChange={pick} />
            </label>
            {file ? (
              <button className="btn btn-secondary mt-3 w-full" type="button" onClick={() => setFile(null)}>
                <X className="h-5 w-5" /> Убрать файл
              </button>
            ) : null}
            <button className="btn btn-primary mt-3 w-full" disabled={!file || analyze.isPending} onClick={() => file && analyze.mutate(file)}>
              Начать анализ
            </button>
          </div>
          <div className="card rounded-lg p-5">
            <h3 className="mb-4 text-lg font-black text-ink">История анализов</h3>
            <div className="space-y-3">
              {history.data?.map((item) => (
                <button key={item.id} className="w-full rounded-lg border border-line bg-white/65 p-4 text-left hover:border-teal" onClick={() => setSelected(item)}>
                  <p className="font-extrabold text-ink">{item.original_filename}</p>
                  <p className="text-sm text-muted">{formatDate(item.created_at)} · {item.status}</p>
                </button>
              ))}
              {!history.data?.length ? <EmptyState icon={FileText} title="История пуста" text="Первый отчет появится после анализа PDF." /> : null}
            </div>
          </div>
        </aside>
        {analyze.isPending ? (
          <LoadingProgress steps={["Загружаем документ", "Читаем PDF", "Подготавливаем страницы", "AI анализирует ЭКГ", "Формируем отчет"]} />
        ) : active ? (
          <ECGReport analysis={active} />
        ) : (
          <EmptyState icon={FileText} title="Выберите PDF" text="Система покажет общий обзор, найденные показатели, вопросы врачу и ограничения анализа." />
        )}
      </div>
    </section>
  );
}
