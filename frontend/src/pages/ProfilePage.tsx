import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";
import type { Profile } from "../types";

const emptyProfile: Partial<Profile> = {
  name: "Азамат",
  age: 38,
  biological_sex: "male",
  height_cm: 176,
  weight_kg: 79,
  activity_level: "Moderate",
  primary_goal: "Общее здоровье",
  health_goals: "",
  known_conditions: "",
  injuries_or_limitations: "",
  dietary_preferences: ""
};

export function ProfilePage() {
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: ["profile"], queryFn: api.getProfile });
  const [form, setForm] = useState<Partial<Profile>>(emptyProfile);

  useEffect(() => {
    if (profile.data) setForm(profile.data);
  }, [profile.data]);

  const mutation = useMutation({
    mutationFn: api.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast.success("Профиль сохранен");
    },
    onError: (error) => toast.error(error.message)
  });

  function update<K extends keyof Profile>(key: K, value: Profile[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate(form);
  }

  return (
    <section>
      <PageHeader title="Профиль здоровья" eyebrow="Основные данные" />
      <form onSubmit={submit} className="grid gap-5 xl:grid-cols-[1fr_0.8fr]">
        <div className="card rounded-lg p-6">
          <h2 className="text-xl font-black text-ink">Основная информация</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label><span className="field-label">Имя</span><input className="field" value={form.name ?? ""} onChange={(e) => update("name", e.target.value)} /></label>
            <label><span className="field-label">Возраст</span><input className="field" type="number" value={form.age ?? ""} onChange={(e) => update("age", Number(e.target.value))} /></label>
            <label><span className="field-label">Пол</span><select className="field" value={form.biological_sex ?? ""} onChange={(e) => update("biological_sex", e.target.value)}><option value="">Не указано</option><option value="male">Мужской</option><option value="female">Женский</option></select></label>
            <label><span className="field-label">Рост, см</span><input className="field" type="number" value={form.height_cm ?? ""} onChange={(e) => update("height_cm", Number(e.target.value))} /></label>
            <label><span className="field-label">Вес, кг</span><input className="field" type="number" value={form.weight_kg ?? ""} onChange={(e) => update("weight_kg", Number(e.target.value))} /></label>
            <label><span className="field-label">Активность</span><select className="field" value={form.activity_level ?? "Moderate"} onChange={(e) => update("activity_level", e.target.value)}><option value="Low">Низкая</option><option value="Moderate">Средняя</option><option value="Active">Активная</option><option value="Very active">Очень активная</option></select></label>
            <label className="md:col-span-2"><span className="field-label">Цель</span><select className="field" value={form.primary_goal ?? "Общее здоровье"} onChange={(e) => update("primary_goal", e.target.value)}><option>Общее здоровье</option><option>Повышение активности</option><option>Поддержание формы</option><option>Улучшение восстановления</option><option>Контроль веса</option></select></label>
          </div>
        </div>

        <div className="space-y-5">
          <div className="card rounded-lg p-6">
            <div className="flex gap-3">
              <ShieldCheck className="mt-1 h-6 w-6 text-teal" />
              <p className="text-sm leading-6 text-muted">Заполняйте только ту информацию, которой готовы поделиться. Эти данные используются для персонализации рекомендаций.</p>
            </div>
          </div>
          <div className="card rounded-lg p-6">
            <h2 className="text-xl font-black text-ink">Здоровье</h2>
            <div className="mt-5 space-y-4">
              <label><span className="field-label">Цели</span><textarea className="field min-h-24" value={form.health_goals ?? ""} onChange={(e) => update("health_goals", e.target.value)} /></label>
              <label><span className="field-label">Особенности здоровья</span><textarea className="field min-h-20" value={form.known_conditions ?? ""} onChange={(e) => update("known_conditions", e.target.value)} /></label>
              <label><span className="field-label">Травмы или ограничения</span><textarea className="field min-h-20" value={form.injuries_or_limitations ?? ""} onChange={(e) => update("injuries_or_limitations", e.target.value)} /></label>
              <label><span className="field-label">Питание</span><textarea className="field min-h-20" value={form.dietary_preferences ?? ""} onChange={(e) => update("dietary_preferences", e.target.value)} /></label>
            </div>
          </div>
          <button className="btn btn-primary w-full" type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Сохраняем..." : "Сохранить профиль"}</button>
        </div>
      </form>
    </section>
  );
}
