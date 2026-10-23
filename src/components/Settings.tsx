import { useEffect, useState } from "react";
import { CheckCircle2, Cloud, Download, MonitorCog, RefreshCw, ShieldCheck, UserRound } from "lucide-react";
import type { Profile, UpdateStatus } from "../types";

export type Preferences = { theme: "light" | "dark"; compact: boolean; automaticUpdates: boolean };

export default function Settings({ profile, preferences, onSave }: { profile: Profile; preferences: Preferences; onSave: (value: Preferences) => void }) {
  const [draft, setDraft] = useState(preferences);
  const [version, setVersion] = useState("0.2.0");
  const [update, setUpdate] = useState<UpdateStatus>({ status: "idle" });
  useEffect(() => { void window.desktop.getVersion().then(setVersion); return window.desktop.onUpdateStatus(setUpdate); }, []);

  async function checkUpdates() {
    setUpdate({ status: "checking" });
    try {
      const result: any = await window.desktop.checkForUpdates();
      if (result?.development) setUpdate({ status: "development", detail: `Modo de desarrollo · ${result.version}` });
    } catch (reason) {
      setUpdate({ status: "error", detail: reason instanceof Error ? reason.message : "No se pudo consultar GitHub." });
    }
  }

  const updateDetail = typeof update.detail === "object" && update.detail ? update.detail : {};
  let projectHost = "No configurado";
  try { projectHost = new URL(import.meta.env.VITE_SUPABASE_URL).hostname; } catch { /* La pantalla sigue disponible para diagnosticar la configuración. */ }
  const statusText: Record<string, string> = {
    idle: "Listo para buscar actualizaciones.", checking: "Buscando actualizaciones…",
    current: "El sistema está actualizado.", available: `Nueva versión disponible: ${updateDetail.version || ""}`,
    downloading: `Descargando… ${Math.round(Number(updateDetail.percent || 0))}%`,
    downloaded: "Actualización descargada y lista para instalar.", development: String(update.detail || "Modo de desarrollo"),
    error: `No se pudo actualizar: ${String(update.detail || "Error desconocido")}`,
  };

  return <section className="page-content settings-page"><header className="page-header"><div><h1>Configuración</h1><p>Administre la apariencia, actualizaciones, conexión y cuenta.</p></div></header>
    <div className="settings-grid">
      <article className="panel"><h2><MonitorCog size={20} /> Apariencia</h2><p className="muted">Personalice cómo se muestra el sistema.</p><label>Tema<select value={draft.theme} onChange={(e) => setDraft({ ...draft, theme: e.target.value as "light" | "dark" })}><option value="light">Claro</option><option value="dark">Oscuro</option></select></label><label className="switch-row"><input type="checkbox" checked={draft.compact} onChange={(e) => setDraft({ ...draft, compact: e.target.checked })} /> Usar menú lateral compacto</label></article>
      <article className="panel"><h2><RefreshCw size={20} /> Actualizaciones</h2><p className="muted">Nuevas versiones firmadas desde GitHub.</p><label className="switch-row"><input type="checkbox" checked={draft.automaticUpdates} onChange={(e) => setDraft({ ...draft, automaticUpdates: e.target.checked })} /> Buscar al iniciar</label><div className="info-list"><span>Versión instalada <strong>{version}</strong></span><span>Repositorio <strong>nexvorytech12/cordon-oro-desktop</strong></span></div><p className="update-status">{statusText[update.status] || update.status}</p><div className="button-row"><button className="button secondary" onClick={() => void checkUpdates()}><RefreshCw size={16} /> Buscar ahora</button>{update.status === "available" && <button className="button gold" onClick={() => void window.desktop.downloadUpdate()}><Download size={16} /> Descargar</button>}{update.status === "downloaded" && <button className="button gold" onClick={() => void window.desktop.installUpdate()}>Instalar y reiniciar</button>}</div></article>
      <article className="panel"><h2><Cloud size={20} /> Conexión</h2><p className="muted">Conexión segura con Supabase.</p><div className="info-list"><span>Estado <strong className="online"><CheckCircle2 size={15} /> Conectado</strong></span><span>Proyecto <strong>{projectHost}</strong></span><span>Entorno <strong>Producción</strong></span></div><p className="muted small"><ShieldCheck size={15} /> La clave publicable nunca se muestra en esta pantalla.</p></article>
      <article className="panel"><h2><UserRound size={20} /> Cuenta y permisos</h2><p className="muted">Datos de la sesión activa.</p><div className="info-list"><span>Usuario <strong>{profile.fullName}</strong></span><span>Correo <strong>{profile.email}</strong></span><span>Rol <strong>{profile.role.replaceAll("_", " ")}</strong></span><span>Permisos <strong>{profile.role === "administrador" ? "Acceso total" : `${profile.permissions.length} asignados`}</strong></span></div></article>
    </div>
    <div className="sticky-actions"><button className="button gold" onClick={() => onSave(draft)}>Guardar configuración</button></div>
  </section>;
}
