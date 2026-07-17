import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";

import { PageHeader } from "../components/PageHeader";
import { api } from "../services/api";
import type { Profile } from "../types";

const emptyProfile: Partial<Profile> = {
  name: "",
  activity_level: "Moderate",
  primary_goal: "Здоровье сердца",
  health_goals: "",
  known_conditions: "",
  injuries_or_limitations: "",
  dietary_preferences: ""
};

/** Optional number field: "" must become null, not 0. */
function numberOrNull(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

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
    onError: (error: Error) => toast.error(error.message)
  });

  function update<K extends keyof Profile>(key: K, value: Profile[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!form.name?.trim()) {
      toast.error("Укажите имя.");
      return;
    }
    // id/user_id/timestamps are server-owned; sending them back is noise at best.
    const { id, user_id, created_at, updated_at, ...payload } = form as Profile;
    mutation.mutate(payload);
  }

  return (
    <section>
      <PageHeader title="Профиль здоровья" eyebrow="Основные данные" />

      <form onSubmit={submit} className="grid gap-5 xl:grid-cols-[1fr_0.8fr]">
        <div className="card rounded-2xl p-6">
          <h2 className="text-xl font-black text-ink">Основная информация</h2>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <label>
              <span className="field-label">Имя</span>
              <input
                className="field text-lg"
                required
                value={form.name ?? ""}
                onChange={(event) => update("name", event.target.value)}
              />
            </label>
            <label>
              <span className="field-label">Возраст</span>
              <input
                className="field text-lg"
                type="number"
                min={18}
                max={120}
                value={form.age ?? ""}
                onChange={(event) => update("age", numberOrNull(event.target.value))}
              />
            </label>
            <label>
              <span className="field-label">Пол</span>
              <select
                className="field text-lg"
                value={form.biological_sex ?? ""}
                onChange={(event) => update("biological_sex", event.target.value || null)}
              >
                <option value="">Не указано</option>
                <option value="male">Мужской</option>
                <option value="female">Женский</option>
              </select>
            </label>
            <label>
              <span className="field-label">Рост, см</span>
              <input
                className="field text-lg"
                type="number"
                min={80}
                max={240}
                value={form.height_cm ?? ""}
                onChange={(event) => update("height_cm", numberOrNull(event.target.value))}
              />
            </label>
            <label>
              <span className="field-label">Вес, кг</span>
              <input
                className="field text-lg"
                type="number"
                min={30}
                max={250}
                value={form.weight_kg ?? ""}
                onChange={(event) => update("weight_kg", numberOrNull(event.target.value))}
              />
            </label>
            <label>
              <span className="field-label">Обычный пульс покоя</span>
              <input
                className="field text-lg"
                type="number"
                min={30}
                max={120}
                placeholder="если знаете"
                value={form.resting_hr_baseline ?? ""}
                onChange={(event) => update("resting_hr_baseline", numberOrNull(event.target.value))}
              />
            </label>
            <label>
              <span className="field-label">Активность</span>
              <select
                className="field text-lg"
                value={form.activity_level ?? "Moderate"}
                onChange={(event) => update("activity_level", event.target.value)}
              >
                <option value="Low">Низкая</option>
                <option value="Moderate">Средняя</option>
                <option value="Active">Активная</option>
                <option value="Very active">Очень активная</option>
              </select>
            </label>
            <label>
              <span className="field-label">Цель</span>
              <select
                className="field text-lg"
                value={form.primary_goal ?? "Здоровье сердца"}
                onChange={(event) => update("primary_goal", event.target.value)}
              >
                <option>Здоровье сердца</option>
                <option>Общее здоровье</option>
                <option>Повышение активности</option>
                <option>Поддержание формы</option>
                <option>Контроль веса</option>
              </select>
            </label>
          </div>
        </div>

        <div className="space-y-5">
          <div className="card rounded-2xl p-6">
            <div className="flex gap-3">
              <ShieldCheck className="mt-1 h-6 w-6 shrink-0 text-teal" aria-hidden="true" />
              <p className="text-base leading-7 text-muted">
                Заполняйте только ту информацию, которой готовы поделиться. Эти данные видите
                только вы, и они используются, чтобы рекомендации подходили именно вам.
              </p>
            </div>
          </div>

          <div className="card rounded-2xl p-6">
            <h2 className="text-xl font-black text-ink">Здоровье</h2>
            <div className="mt-5 space-y-4">
              <label>
                <span className="field-label">Цели</span>
                <textarea
                  className="field min-h-24 text-lg"
                  value={form.health_goals ?? ""}
                  onChange={(event) => update("health_goals", event.target.value)}
                />
              </label>
              <label>
                <span className="field-label">Особенности здоровья</span>
                <textarea
                  className="field min-h-20 text-lg"
                  placeholder="например: гипертония, диабет"
                  value={form.known_conditions ?? ""}
                  onChange={(event) => update("known_conditions", event.target.value)}
                />
              </label>
              <label>
                <span className="field-label">Травмы или ограничения</span>
                <textarea
                  className="field min-h-20 text-lg"
                  value={form.injuries_or_limitations ?? ""}
                  onChange={(event) => update("injuries_or_limitations", event.target.value)}
                />
              </label>
              <label>
                <span className="field-label">Питание</span>
                <textarea
                  className="field min-h-20 text-lg"
                  value={form.dietary_preferences ?? ""}
                  onChange={(event) => update("dietary_preferences", event.target.value)}
                />
              </label>
            </div>
          </div>

          <button className="btn btn-primary w-full text-lg" type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Сохраняем…" : "Сохранить профиль"}
          </button>
        </div>
      </form>
    </section>
  );
}
