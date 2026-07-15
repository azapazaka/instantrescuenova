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
      <PageHeader title="Профиль здоровья" eyebrow="Personal information" />
      <form onSubmit={submit} className="grid gap-5 xl:grid-cols-[1fr_0.8fr]">
        <div className="card rounded-lg p-6">
          <h2 className="text-xl font-black text-ink">Основная информация</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label><span className="field-label">Name</span><input className="field" value={form.name ?? ""} onChange={(e) => update("name", e.target.value)} /></label>
            <label><span className="field-label">Age</span><input className="field" type="number" value={form.age ?? ""} onChange={(e) => update("age", Number(e.target.value))} /></label>
            <label><span className="field-label">Biological sex optional</span><select className="field" value={form.biological_sex ?? ""} onChange={(e) => update("biological_sex", e.target.value)}><option value="">Не указано</option><option value="male">Male</option><option value="female">Female</option></select></label>
            <label><span className="field-label">Height, cm</span><input className="field" type="number" value={form.height_cm ?? ""} onChange={(e) => update("height_cm", Number(e.target.value))} /></label>
            <label><span className="field-label">Weight, kg</span><input className="field" type="number" value={form.weight_kg ?? ""} onChange={(e) => update("weight_kg", Number(e.target.value))} /></label>
            <label><span className="field-label">Activity level</span><select className="field" value={form.activity_level ?? "Moderate"} onChange={(e) => update("activity_level", e.target.value)}><option>Low</option><option>Moderate</option><option>Active</option><option>Very active</option></select></label>
            <label className="md:col-span-2"><span className="field-label">Primary goal</span><select className="field" value={form.primary_goal ?? "Общее здоровье"} onChange={(e) => update("primary_goal", e.target.value)}><option>Общее здоровье</option><option>Повышение активности</option><option>Поддержание формы</option><option>Улучшение восстановления</option><option>Контроль веса</option></select></label>
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
            <h2 className="text-xl font-black text-ink">Health Context</h2>
            <div className="mt-5 space-y-4">
              <label><span className="field-label">Health goals</span><textarea className="field min-h-24" value={form.health_goals ?? ""} onChange={(e) => update("health_goals", e.target.value)} /></label>
              <label><span className="field-label">Known conditions optional</span><textarea className="field min-h-20" value={form.known_conditions ?? ""} onChange={(e) => update("known_conditions", e.target.value)} /></label>
              <label><span className="field-label">Injuries or limitations optional</span><textarea className="field min-h-20" value={form.injuries_or_limitations ?? ""} onChange={(e) => update("injuries_or_limitations", e.target.value)} /></label>
              <label><span className="field-label">Dietary preferences optional</span><textarea className="field min-h-20" value={form.dietary_preferences ?? ""} onChange={(e) => update("dietary_preferences", e.target.value)} /></label>
            </div>
          </div>
          <button className="btn btn-primary w-full" type="submit" disabled={mutation.isPending}>{mutation.isPending ? "Сохраняем..." : "Сохранить профиль"}</button>
        </div>
      </form>
    </section>
  );
}
