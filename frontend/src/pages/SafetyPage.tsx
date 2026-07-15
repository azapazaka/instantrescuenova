import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, Plus, Radio, ShieldCheck, Trash2 } from "lucide-react";
import { FormEvent, useState } from "react";
import { toast } from "sonner";

import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { api } from "../services/api";
import { formatDate, formatTime } from "../utils/format";

export function SafetyPage() {
  const queryClient = useQueryClient();
  const contacts = useQuery({ queryKey: ["contacts"], queryFn: api.listContacts });
  const devices = useQuery({ queryKey: ["devices"], queryFn: api.listDevices });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.listIncidents });
  const [contactForm, setContactForm] = useState({ name: "", relationship: "" });

  const refreshSafety = () => {
    queryClient.invalidateQueries({ queryKey: ["contacts"] });
    queryClient.invalidateQueries({ queryKey: ["devices"] });
    queryClient.invalidateQueries({ queryKey: ["incidents"] });
  };

  const addContact = useMutation({
    mutationFn: api.addContact,
    onSuccess: () => {
      setContactForm({ name: "", relationship: "" });
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
    mutationFn: () => api.addDevice("Demo Safety Band"),
    onSuccess: (device) => {
      refreshSafety();
      toast.success(`Устройство создано. Secret: ${device.device_secret}`);
    },
    onError: (error) => toast.error(error.message)
  });

  const simulate = useMutation({
    mutationFn: api.simulateFall,
    onSuccess: () => {
      refreshSafety();
      toast.success("Demo fall incident создан");
    },
    onError: (error) => toast.error(error.message)
  });

  function submitContact(event: FormEvent) {
    event.preventDefault();
    if (!contactForm.name.trim() || !contactForm.relationship.trim()) return;
    addContact.mutate(contactForm);
  }

  const connectedContacts = contacts.data?.filter((contact) => contact.status === "connected").length ?? 0;

  return (
    <section>
      <PageHeader title="Безопасность" eyebrow="Fall detection and alerts">
        <button className="btn btn-danger" onClick={() => simulate.mutate()} disabled={simulate.isPending}>
          <BellRing className="h-5 w-5" />
          Simulate Fall
        </button>
      </PageHeader>

      <div className="grid gap-5 md:grid-cols-3">
        <div className="card rounded-lg p-5">
          <ShieldCheck className="mb-4 h-8 w-8 text-teal" />
          <p className="text-sm font-extrabold uppercase tracking-wide text-teal">Safety Overview</p>
          <h2 className="mt-2 text-2xl font-black text-ink">{contacts.data?.length || devices.data?.length ? "Система безопасности активна" : "Настройте safety flow"}</h2>
        </div>
        <div className="card rounded-lg p-5">
          <p className="text-sm font-bold text-muted">Устройства</p>
          <p className="mt-2 text-3xl font-black text-ink">{devices.data?.length ?? 0}</p>
          <button className="btn btn-secondary mt-4 w-full" onClick={() => addDevice.mutate()} disabled={addDevice.isPending}>
            <Radio className="h-5 w-5" />
            Добавить demo device
          </button>
        </div>
        <div className="card rounded-lg p-5">
          <p className="text-sm font-bold text-muted">Telegram contacts</p>
          <p className="mt-2 text-3xl font-black text-ink">{connectedContacts}/{contacts.data?.length ?? 0}</p>
          <p className="mt-2 text-sm leading-6 text-muted">Connected contacts смогут получать alert, когда Telegram настроен.</p>
        </div>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-5">
          <form onSubmit={submitContact} className="card rounded-lg p-6">
            <h2 className="text-xl font-black text-ink">Emergency contacts</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <label><span className="field-label">Name</span><input className="field" value={contactForm.name} onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })} /></label>
              <label><span className="field-label">Relationship</span><input className="field" value={contactForm.relationship} onChange={(e) => setContactForm({ ...contactForm, relationship: e.target.value })} /></label>
            </div>
            <button className="btn btn-primary mt-4 w-full" type="submit" disabled={addContact.isPending}>
              <Plus className="h-5 w-5" /> Add contact
            </button>
          </form>

          <div className="card rounded-lg p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Contacts</h3>
            <div className="space-y-3">
              {contacts.data?.map((contact) => (
                <div key={contact.id} className="rounded-lg border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-extrabold text-ink">{contact.name}</p>
                      <p className="text-sm text-muted">{contact.relationship}</p>
                    </div>
                    <StatusBadge value={contact.status} label={contact.status === "connected" ? "Connected" : "Waiting for connection"} />
                  </div>
                  <div className="mt-4 rounded-lg bg-ink p-4 text-white">
                    <p className="text-xs font-bold uppercase tracking-wide text-white/55">Telegram pairing</p>
                    <p className="mt-2 text-sm">Откройте Telegram-бота Caspian Care и отправьте:</p>
                    <code className="mt-2 block text-xl font-black">/start {contact.pairing_code}</code>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button className="btn btn-secondary" onClick={() => testContact.mutate(contact.id)}>Send test</button>
                    <button className="btn btn-secondary" onClick={() => regenerate.mutate(contact.id)}>Reconnect</button>
                    <button className="btn bg-emergency/10 text-emergency" onClick={() => deleteContact.mutate(contact.id)} aria-label="Remove contact">
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
              {!contacts.data?.length ? <EmptyState icon={ShieldCheck} title="Контактов пока нет" text="Добавьте близкого человека, чтобы увидеть pairing flow." /> : null}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="card rounded-lg p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Devices</h3>
            <div className="space-y-3">
              {devices.data?.map((device) => (
                <div key={device.id} className="rounded-lg border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-extrabold text-ink">{device.name}</p>
                      <p className="text-sm text-muted">{device.device_id}</p>
                    </div>
                    <StatusBadge value={device.status} />
                  </div>
                </div>
              ))}
              {!devices.data?.length ? <EmptyState icon={Radio} title="Нет подключенных устройств" text="Создайте demo device для будущего ESP32 flow." /> : null}
            </div>
          </div>

          <div className="card rounded-lg p-5">
            <h3 className="mb-4 text-lg font-black text-ink">Recent incidents</h3>
            <div className="space-y-3">
              {incidents.data?.map((incident) => (
                <div key={incident.id} className="rounded-lg border border-line bg-white/65 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-extrabold text-ink">Possible fall detected</p>
                      <p className="text-sm text-muted">{formatDate(incident.event_timestamp)} · {formatTime(incident.event_timestamp)}</p>
                    </div>
                    <StatusBadge value="detected" label={incident.telegram_notification_status.replace(/_/g, " ")} />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted">Confidence: {incident.confidence ? Math.round(incident.confidence * 100) : "n/a"}%</p>
                </div>
              ))}
              {!incidents.data?.length ? <EmptyState icon={BellRing} title="Инцидентов нет" text="Simulate Fall создаст запись через backend service." /> : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
