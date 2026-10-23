import { useEffect, useState, type FormEvent } from "react";
import { X } from "lucide-react";
import type { FieldDefinition } from "../types";

export default function RecordModal({ title, fields, initial = {}, busy, onClose, onSave }: {
  title: string;
  fields: FieldDefinition[];
  initial?: Record<string, any>;
  busy?: boolean;
  onClose: () => void;
  onSave: (values: Record<string, any>) => void | Promise<void>;
}) {
  const [values, setValues] = useState<Record<string, any>>({});
  useEffect(() => {
    const next: Record<string, any> = {};
    for (const field of fields) {
      next[field.key] = initial[field.key] ?? (field.type === "boolean" ? field.key === "is_active" : "");
    }
    setValues(next);
  }, [fields, initial]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const normalized = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value === "" ? null : value]));
    void onSave(normalized);
  }

  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
    <form className="modal" onSubmit={submit}>
      <header><h2>{title}</h2><button type="button" className="icon-button" onClick={onClose}><X /></button></header>
      <div className="form-grid">
        {fields.map((field) => <label key={field.key} className={field.type === "textarea" ? "span-2" : ""}>{field.label}{field.required && " *"}
          {field.type === "textarea" ? <textarea value={values[field.key] ?? ""} onChange={(e) => setValues({ ...values, [field.key]: e.target.value })} required={field.required} />
            : field.type === "select" ? <select value={values[field.key] ?? ""} onChange={(e) => setValues({ ...values, [field.key]: e.target.value })} required={field.required}><option value="">Seleccione…</option>{field.options?.map((option) => <option key={option}>{option}</option>)}</select>
            : field.type === "boolean" ? <span className="checkbox-row"><input type="checkbox" checked={Boolean(values[field.key])} onChange={(e) => setValues({ ...values, [field.key]: e.target.checked })} /> Sí</span>
            : <input type={field.type === "number" ? "number" : field.type === "date" ? "date" : field.type === "password" ? "password" : "text"} step={field.type === "number" ? "0.01" : undefined} value={values[field.key] ?? ""} onChange={(e) => setValues({ ...values, [field.key]: field.type === "number" ? Number(e.target.value) : e.target.value })} required={field.required} />}
        </label>)}
      </div>
      <footer><button type="button" className="button ghost" onClick={onClose}>Cancelar</button><button className="button gold" disabled={busy}>{busy ? "Guardando…" : "Guardar"}</button></footer>
    </form>
  </div>;
}
