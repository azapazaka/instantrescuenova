import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, Plus, Radio, ShieldCheck, Trash2 } from "lucide-react";
import { FormEvent, useState } from "react";
import { toast } from "sonner";

import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import { formatDate, formatTime } from "../utils/format";

const notificationLabel: Record<string, string> = {
  no_contacts: "нет контактов",
  not_configured: "не настроено",
  sent: "отправлено",
  partially_failed: "частично отправлено"
};

export function SafetyPage() {
  const queryClient = useQueryClient();
  const contacts = useQuery({ queryKey: ["contacts"], queryFn: api.listContacts });
  const devices = useQuery({ queryKey: ["devices"], queryFn: api.listDevices });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.listIncidents });
  const [contactForm, setContactForm] = useState({ name: "", relationship: "", telegram_username: "" });

  const refreshSafety = () => {
    queryClient.invalidateQueries({ queryKey: ["contacts"] });
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    queryClient.invalidateQueries({ queryKey: ["incidents"] });
  };

  const addContact = useMutation({
    mutationFn: api.addContact,
    onSuccess: () => {
      setContactForm({ name: "", relationship: "", telegram_username: "" });
      refreshSafety();
      toast.success("Контакт добавлен");
    },
    onError: (error) => toast.error(error.message)
  });

  const deleteContact = useMutation({
    mutationFn: api.deleteContact,
    onSuccess: () => {
      refreshSafety();
      toast.success("Контакт удален");
    },
    onError: (error) => toast.error(error.message)
  });

  const testContact = useMutation({
    mutationFn: api.testContact,
    onSuccess: (data) => toast(data.message),
    onError: (error) => toast.error(error.message)
  });

  const regenerate = useMutation({
    mutationFn: api.regeneratePairing,
    onSuccess: () => {
      refreshSafety();
      toast.success("Pairing code обновлен");
    },
    onError: (error) => toast.error(error.message)
  });

  const addDevice = useMutation({
    mutationFn: () => api.addDevice("Браслет безопасности"),
    onSuccess: (device) => {
      refreshSafety();
      toast.success(`Устройство добавлено. Код: ${device.device_secret}`);
    },
    onError: (error) => toast.error(error.message)
  });

  const simulate = useMutation({
    mutationFn: api.simulateFall,
    onSuccess: () => {
      refreshSafety();
      toast.success("Проверка записана");
    },
    onError: (error) => toast.error(error.message)
  });

  function submitContact(event: FormEvent) {
    event.preventDefault();
    if (!contactForm.name.trim() || !contactForm.relationship.trim() || !contactForm.telegram_username.trim()) return;
    addContact.mutate(contactForm);
  }

  const connectedContacts = contacts.data?.filter((contact) => contact.status === "connected").length ?? 0;

  return (
    <section>
      <PageHeader title="Безопасность" eyebrow="Контакты и уведомления">
        <button className="btn btn-danger" onClick={() => simulate.mutate()} disabled={simulate.isPending}>
          <BellRing className="h-5 w-5" />
          Проверить падение
        </button>
      </PageHeader>

      <div className="grid gap-5 md:grid-cols-3">
        <div className="card rounded-lg p-5">
          <ShieldCheck className="mb-4 h-8 w-8 text-teal" />
          <p className="text-sm font-extrabold uppercase tracking-wide text-teal">Статус</p>
          <h2 className="mt-2 text-2xl font-black text-ink">{contacts.data?.length || devices.data?.length ? "Защита активна" : "Добавьте контакт"}</h2>
        </div>
        <div className="card rounded-lg p-5">
          <p className="text-sm font-bold text-muted">Устройства</p>
          <p className="mt-2 text-3xl font-black text-ink">{devices.data?.length ?? 0}</p>
          <button className="btn btn-secondary mt-4 w-full" onClick={() => addDevice.mutate()} disabled={addDevice.isPending}>
            <Radio className="h-5 w-5" />
            Добавить устройство
          </button>
        </div>
        <div className="card rounded-lg p-5">
          <p className="text-sm font-bold text-muted">Контакты</p>
          <p className="mt-2 text-3xl font-black text-ink">{connectedContacts}/{contacts.data?.length ?? 0}</p>
          <p className="mt-2 text-sm leading-6 text-muted">Подключенные контакты получают уведомления.</p>
        </div>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-5">
          <form onSubmit={submitContact} className="card rounded-lg p-6">
            <h2 className="text-xl font-black text-ink">Близкие контакты</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              <label><span className="field-label">Имя</span><input className="field" value={contactForm.name} onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })} /></label>
              <label><span className="field-label">Кем приходится</span><input className="field" value={contactForm.relationship} onChange={(e) => setContactForm({ ...contactForm, relationship: e.target.value })} /></label>
              <label><span className="field-label">Telegram username</span><input className="field" placeholder="@username" value={contactForm.telegram_username} onChange={(e) => setContactForm({ ...contactForm, telegram_username: e.target.value })} /></label>
            </div>
            <button className="btn btn-primary mt-4 w-full" type="submit" disabled={addContact.isPending}>
              <Plus className="h-5 w-5" /> Добавить контакт
            </button>
          </form>

          <div className="card rounded-lg p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Контакты</h3>
            <div className="space-y-3">
              {contacts.data?.map((contact) => (
                <div key={contact.id} className="rounded-lg border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-extrabold text-ink">{contact.name}</p>
                      <p className="text-sm text-muted">{contact.relationship}{contact.telegram_username ? ` · ${contact.telegram_username}` : ""}</p>
                    </div>
                    <StatusBadge value={contact.status} label={contact.status === "connected" ? "Подключен" : "Ожидает"} />
                  </div>
                  <div className="mt-4 rounded-lg bg-ink p-4 text-white">
                    <p className="mt-2 text-sm">Откройте Telegram-бота Caspian Care и отправьте:</p>
                    <code className="mt-2 block text-xl font-black">/start {contact.pairing_code}</code>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button className="btn btn-secondary" onClick={() => testContact.mutate(contact.id)}>Тест</button>
                    <button className="btn btn-secondary" onClick={() => regenerate.mutate(contact.id)}>Новый код</button>
                    <button className="btn bg-emergency/10 text-emergency" onClick={() => deleteContact.mutate(contact.id)} aria-label="Remove contact">
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
              {!contacts.data?.length ? <EmptyState icon={ShieldCheck} title="Контактов пока нет" text="Добавьте близкого человека." /> : null}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="card rounded-lg p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Устройства</h3>
            <div className="space-y-3">
              {devices.data?.map((device) => (
                <div key={device.id} className="rounded-lg border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-extrabold text-ink">{device.name}</p>
                      <p className="text-sm text-muted">{device.device_id}</p>
                    </div>
                    <StatusBadge value={device.status} label={device.status === "active" ? "Активно" : device.status} />
                  </div>
                </div>
              ))}
              {!devices.data?.length ? <EmptyState icon={Radio} title="Устройств нет" text="Добавьте устройство для проверки." /> : null}
            </div>
          </div>

          <div className="card rounded-lg p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Последние инциденты</h3>
            <div className="space-y-3">
              {incidents.data?.map((incident) => (
                <div key={incident.id} className="rounded-lg border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-extrabold text-ink">Возможное падение</p>
                      <p className="text-sm text-muted">{formatDate(incident.event_timestamp)} · {formatTime(incident.event_timestamp)}</p>
                    </div>
                    <StatusBadge value="detected" label={notificationLabel[incident.telegram_notification_status] ?? incident.telegram_notification_status} />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted">Уверенность: {incident.confidence ? Math.round(incident.confidence * 100) : "не указана"}%</p>
                </div>
              ))}
              {!incidents.data?.length ? <EmptyState icon={BellRing} title="Инцидентов нет" text="Нажмите проверку падения." /> : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
