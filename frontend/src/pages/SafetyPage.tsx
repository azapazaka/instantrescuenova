import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, Check, Copy, Plus, Radio, Send, ShieldCheck, Trash2, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import { formatDate, formatTime } from "../utils/format";

/** Delivery status, worded so a failure reads as a failure. */
const notificationLabel: Record<string, string> = {
  no_contacts: "некому отправить",
  not_configured: "уведомления недоступны",
  sent: "доставлено",
  partially_failed: "доставлено не всем",
  failed: "не доставлено"
};

const notificationTone: Record<string, string> = {
  sent: "connected",
  partially_failed: "waiting",
  not_configured: "waiting",
  no_contacts: "detected",
  failed: "detected"
};

export function SafetyPage() {
  const queryClient = useQueryClient();
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, staleTime: Infinity });
  const contacts = useQuery({ queryKey: ["contacts"], queryFn: api.listContacts });
  const devices = useQuery({ queryKey: ["devices"], queryFn: api.listDevices });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.listIncidents });

  const [contactForm, setContactForm] = useState({ name: "", relationship: "", telegram_username: "" });
  const [copied, setCopied] = useState<number | null>(null);

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
    onError: (error: Error) => toast.error(error.message)
  });

  const deleteContact = useMutation({
    mutationFn: api.deleteContact,
    onSuccess: () => {
      refreshSafety();
      toast.success("Контакт удален");
    },
    onError: (error: Error) => toast.error(error.message)
  });

  const testContact = useMutation({
    mutationFn: api.testContact,
    // The backend now reports real delivery, so surface failure as failure.
    onSuccess: (data) => (data.ok ? toast.success(data.message) : toast.error(data.message)),
    onError: (error: Error) => toast.error(error.message)
  });

  const regenerate = useMutation({
    mutationFn: api.regeneratePairing,
    onSuccess: () => {
      refreshSafety();
      toast.success("Код обновлен");
    },
    onError: (error: Error) => toast.error(error.message)
  });

  const addDevice = useMutation({
    mutationFn: () => api.addDevice("Браслет безопасности"),
    onSuccess: (device) => {
      refreshSafety();
      // The secret is shown once and never retrievable again.
      toast.success(`Устройство добавлено. Сохраните код: ${device.device_secret}`, { duration: 15000 });
    },
    onError: (error: Error) => toast.error(error.message)
  });

  const simulate = useMutation({
    mutationFn: api.simulateFall,
    onSuccess: (incident) => {
      refreshSafety();
      const status = incident.telegram_notification_status;
      if (status === "sent") toast.success("Уведомление отправлено близким");
      else toast.error(`Инцидент записан, но: ${notificationLabel[status] ?? status}`);
    },
    onError: (error: Error) => toast.error(error.message)
  });

  function submitContact(event: FormEvent) {
    event.preventDefault();
    if (!contactForm.name.trim() || !contactForm.relationship.trim()) return;
    addContact.mutate(contactForm);
  }

  function getInviteLink(code: string) {
    return `https://t.me/${botUsername}?start=${code}`;
  }

  function getShareLink(contactName: string, inviteLink: string) {
    const text = `${contactName}, подключитесь к Instant Rescue, чтобы получать уведомления о падении.`;
    return `https://t.me/share/url?url=${encodeURIComponent(inviteLink)}&text=${encodeURIComponent(text)}`;
  }

  async function copyInvite(id: number, inviteLink: string) {
    await navigator.clipboard.writeText(inviteLink);
    setCopied(id);
    toast.success("Ссылка приглашения скопирована");
    setTimeout(() => setCopied(null), 2000);
  }

  const connected = contacts.data?.filter((contact) => contact.status === "connected").length ?? 0;
  const telegramConfigured = health.data?.telegram_configured ?? false;
  const botUsername = telegramConfigured ? health.data?.telegram_bot_username ?? "" : "";

  return (
    <section>
      <PageHeader title="Безопасность" eyebrow="Контакты и уведомления">
        <button
          className="btn btn-danger text-base"
          onClick={() => simulate.mutate()}
          disabled={simulate.isPending}
        >
          <BellRing className="h-5 w-5" aria-hidden="true" />
          Проверить падение
        </button>
      </PageHeader>

      {health.data && !telegramConfigured ? (
        <div className="mb-5 flex items-start gap-3 rounded-2xl border-2 border-amber/40 bg-amber/10 p-4">
          <X className="mt-0.5 h-5 w-5 shrink-0 text-amber" aria-hidden="true" />
          <p className="text-base leading-7 text-amber">
            <strong>Telegram-уведомления временно недоступны.</strong> Контакты и
            устройства можно добавить сейчас; отправка уведомлений включится
            автоматически после подключения бота.
          </p>
        </div>
      ) : null}

      <div className="grid gap-5 md:grid-cols-3">
        <div className="card rounded-2xl p-5">
          <ShieldCheck className="mb-3 h-8 w-8 text-teal" aria-hidden="true" />
          <p className="text-sm font-extrabold uppercase tracking-wide text-teal">Статус</p>
          <h2 className="mt-2 text-2xl font-black text-ink">
            {connected > 0 ? "Защита активна" : telegramConfigured ? "Подключите Telegram" : "Уведомления готовятся"}
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            {connected > 0
              ? "Близкие получат уведомление о падении."
              : telegramConfigured
                ? "Пока никто не получит уведомление о падении."
                : "Пока падения записываются в журнал без отправки в Telegram."}
          </p>
        </div>
        <div className="card rounded-2xl p-5">
          <p className="text-sm font-bold text-muted">Устройства</p>
          <p className="mt-2 text-3xl font-black text-ink">{devices.data?.length ?? 0}</p>
          <button
            className="btn btn-secondary mt-4 w-full"
            onClick={() => addDevice.mutate()}
            disabled={addDevice.isPending}
          >
            <Radio className="h-5 w-5" aria-hidden="true" />
            Добавить устройство
          </button>
        </div>
        <div className="card rounded-2xl p-5">
          <p className="text-sm font-bold text-muted">Подключенные контакты</p>
          <p className="mt-2 text-3xl font-black text-ink">
            {connected}/{contacts.data?.length ?? 0}
          </p>
          <p className="mt-2 text-sm leading-6 text-muted">
            Уведомления приходят только подключенным контактам.
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <div className="space-y-5">
          <form onSubmit={submitContact} className="card rounded-2xl p-6">
            <h2 className="text-xl font-black text-ink">Добавить близкого</h2>
            <div className="mt-5 grid gap-4">
              <label>
                <span className="field-label">Имя</span>
                <input
                  className="field text-lg"
                  value={contactForm.name}
                  onChange={(event) => setContactForm({ ...contactForm, name: event.target.value })}
                />
              </label>
              <label>
                <span className="field-label">Кем приходится</span>
                <input
                  className="field text-lg"
                  value={contactForm.relationship}
                  onChange={(event) => setContactForm({ ...contactForm, relationship: event.target.value })}
                />
              </label>
              <label>
                <span className="field-label">Telegram (необязательно)</span>
                <input
                  className="field text-lg"
                  placeholder="@username"
                  value={contactForm.telegram_username}
                  onChange={(event) =>
                    setContactForm({ ...contactForm, telegram_username: event.target.value })
                  }
                />
              </label>
            </div>
            <button className="btn btn-primary mt-4 w-full text-lg" type="submit" disabled={addContact.isPending}>
              <Plus className="h-5 w-5" aria-hidden="true" /> Добавить контакт
            </button>
          </form>

          <div className="card rounded-2xl p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Контакты</h3>
            <div className="space-y-3">
              {contacts.data?.map((contact) => (
                <div key={contact.id} className="rounded-xl border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-lg font-extrabold text-ink">{contact.name}</p>
                      <p className="text-sm text-muted">
                        {contact.relationship}
                        {contact.telegram_username ? ` · ${contact.telegram_username}` : ""}
                      </p>
                    </div>
                    <StatusBadge
                      value={contact.status}
                      label={contact.status === "connected" ? "Подключен" : "Ожидает"}
                    />
                  </div>

                  {contact.status === "connected" ? (
                    <p className="mt-3 flex items-center gap-2 rounded-lg bg-mint/60 p-3 text-sm font-bold text-spruce">
                      <Check className="h-4 w-4" aria-hidden="true" />
                      Telegram подключен — уведомления придут сюда.
                    </p>
                  ) : telegramConfigured && botUsername ? (
                    <div className="mt-4 rounded-xl bg-ink p-4 text-white">
                      {(() => {
                        const inviteLink = getInviteLink(contact.pairing_code);
                        return (
                          <>
                            <p className="text-sm leading-6 text-white/85">
                              Отправьте близкому приглашение в Telegram. Ему останется нажать
                              Start у <strong className="text-white">@{botUsername}</strong>, и контакт
                              подключится автоматически.
                            </p>
                            <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                              <a
                                className="btn btn-primary flex-1 justify-center"
                                href={getShareLink(contact.name, inviteLink)}
                                target="_blank"
                                rel="noreferrer noopener"
                              >
                                <Send className="h-5 w-5" aria-hidden="true" />
                                Отправить приглашение
                              </a>
                              <button
                                type="button"
                                onClick={() => copyInvite(contact.id, inviteLink)}
                                className="btn bg-white/15 text-white hover:bg-white/25"
                              >
                                {copied === contact.id ? (
                                  <Check className="h-5 w-5" aria-hidden="true" />
                                ) : (
                                  <Copy className="h-5 w-5" aria-hidden="true" />
                                )}
                                {copied === contact.id ? "Скопировано" : "Скопировать ссылку"}
                              </button>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  ) : (
                    <p className="mt-3 rounded-lg bg-amber/10 p-3 text-sm font-bold leading-6 text-amber">
                      Контакт сохранён. Код подключения станет доступен после включения Telegram-уведомлений.
                    </p>
                  )}

                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      className="btn btn-secondary"
                      onClick={() => testContact.mutate(contact.id)}
                      disabled={testContact.isPending}
                    >
                      Проверить связь
                    </button>
                    <button className="btn btn-secondary" onClick={() => regenerate.mutate(contact.id)}>
                      Новый код
                    </button>
                    <button
                      className="btn bg-emergency/10 text-emergency"
                      onClick={() => deleteContact.mutate(contact.id)}
                      aria-label={`Удалить контакт ${contact.name}`}
                    >
                      <Trash2 className="h-5 w-5" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              ))}
              {!contacts.data?.length ? (
                <EmptyState icon={ShieldCheck} title="Контактов пока нет" text="Добавьте близкого человека." />
              ) : null}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="card rounded-2xl p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Устройства</h3>
            <div className="space-y-3">
              {devices.data?.map((device) => (
                <div key={device.id} className="rounded-xl border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-extrabold text-ink">{device.name}</p>
                      <p className="text-sm text-muted">{device.device_id}</p>
                    </div>
                    <StatusBadge value={device.status} label={device.status === "active" ? "Активно" : device.status} />
                  </div>
                </div>
              ))}
              {!devices.data?.length ? (
                <EmptyState icon={Radio} title="Устройств нет" text="Датчик падения подключается здесь." />
              ) : null}
            </div>
          </div>

          <div className="card rounded-2xl p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Последние инциденты</h3>
            <div className="space-y-3">
              {incidents.data?.map((incident) => (
                <div key={incident.id} className="rounded-xl border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-lg font-extrabold text-ink">Возможное падение</p>
                      <p className="text-sm text-muted">
                        {formatDate(incident.event_timestamp)} · {formatTime(incident.event_timestamp)}
                      </p>
                    </div>
                    <StatusBadge
                      value={notificationTone[incident.telegram_notification_status] ?? "detected"}
                      label={
                        notificationLabel[incident.telegram_notification_status] ??
                        incident.telegram_notification_status
                      }
                    />
                  </div>

                  <p className="mt-3 text-sm leading-6 text-muted">
                    Уверенность датчика:{" "}
                    {incident.confidence ? `${Math.round(incident.confidence * 100)}%` : "не указана"}
                    {typeof incident.hr_context?.bpm === "number"
                      ? ` · пульс ${Math.round(incident.hr_context.bpm as number)} уд/мин`
                      : ""}
                  </p>

                  {incident.notification_detail?.length ? (
                    <ul className="mt-3 space-y-1 border-t border-line pt-3">
                      {incident.notification_detail.map((attempt) => (
                        <li
                          key={attempt.contact_id}
                          className="flex items-start gap-2 text-sm leading-6 text-muted"
                        >
                          {attempt.ok ? (
                            <Check className="mt-1 h-4 w-4 shrink-0 text-spruce" aria-hidden="true" />
                          ) : (
                            <X className="mt-1 h-4 w-4 shrink-0 text-emergency" aria-hidden="true" />
                          )}
                          <span>
                            <strong className="text-ink">{attempt.contact_name}</strong>: {attempt.detail}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              ))}
              {!incidents.data?.length ? (
                <EmptyState icon={BellRing} title="Инцидентов нет" text="Нажмите «Проверить падение»." />
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
