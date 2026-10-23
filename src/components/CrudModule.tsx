import { useCallback, useEffect, useMemo, useState } from "react";
import { Download, Edit3, MessageCircle, Plus, RefreshCw, Settings2, Trash2 } from "lucide-react";
import { can, supabase } from "../lib/supabase";
import type { FieldDefinition, ModuleDefinition, Profile } from "../types";
import RecordModal from "./RecordModal";

type ActionState = { title: string; fields: FieldDefinition[]; initial?: Record<string, any>; submit: (values: Record<string, any>) => Promise<void> };

function nested(row: Record<string, any>, key: string): any {
  return key.split(".").reduce((value, part) => {
    if (Array.isArray(value)) value = value[0];
    return value && typeof value === "object" ? value[part] : null;
  }, row as any);
}

function formatValue(value: any, format?: string) {
  if (format === "money") return new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN" }).format(Number(value || 0));
  if (format === "boolean") return value ? "Sí" : "No";
  if (format === "date" && value) return new Date(String(value).length === 10 ? `${value}T00:00:00` : value).toLocaleDateString("es-PE");
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return value.name || value.full_name || "";
  return String(value).replaceAll("_", " ");
}

function toBase64(text: string) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary);
}

export default function CrudModule({ definition, profile, refreshToken }: { definition: ModuleDefinition; profile: Profile; refreshToken: number }) {
  const [rows, setRows] = useState<Record<string, any>[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState<{ mode: "create" | "edit"; row?: Record<string, any> } | null>(null);
  const [action, setAction] = useState<ActionState | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const writable = can(profile, definition.permission);
  const selected = rows.find((row) => row.id === selectedId);

  const refresh = useCallback(async () => {
    setLoading(true);
    let request = supabase.from(definition.table).select(definition.select || "*").limit(500);
    request = request.order("created_at", { ascending: false });
    const { data, error: requestError } = await request;
    if (requestError) setError(requestError.message);
    else { setRows((data as Record<string, any>[]) || []); setError(""); }
    setLoading(false);
  }, [definition]);

  useEffect(() => { void refresh(); }, [refresh, refreshToken]);

  const filtered = useMemo(() => {
    const term = query.trim().toLocaleLowerCase("es");
    if (!term) return rows;
    return rows.filter((row) => JSON.stringify(row).toLocaleLowerCase("es").includes(term));
  }, [query, rows]);

  async function save(values: Record<string, any>) {
    setBusy(true); setError("");
    const result = modal?.mode === "create" && definition.table === "profiles"
      ? await supabase.functions.invoke("create-user", { body: values })
      : modal?.mode === "edit" && modal.row
        ? await supabase.from(definition.table).update(values).eq("id", modal.row.id)
        : await supabase.from(definition.table).insert(values);
    setBusy(false);
    if (result.error) return setError(result.error.message);
    setModal(null); await refresh();
  }

  async function deactivate() {
    if (!selected || !window.confirm("¿Desactivar el registro seleccionado?")) return;
    const { error: updateError } = await supabase.from(definition.table).update({ is_active: false }).eq("id", selected.id);
    if (updateError) setError(updateError.message); else await refresh();
  }

  async function performAction(kind: NonNullable<ModuleDefinition["actions"]>[number]) {
    if (!selected) return setError("Seleccione primero una fila.");
    if (kind === "whatsapp") {
      let phone = String(selected.whatsapp || selected.phone || "").replace(/\D/g, "");
      if (phone.length === 9) phone = "51" + phone;
      if (!phone) return setError("El cliente no tiene teléfono o WhatsApp.");
      await window.desktop.openExternal(`https://wa.me/${phone}?text=${encodeURIComponent("Hola, le escribe Cordón de Oro.")}`);
      return;
    }
    if (kind === "convert") {
      if (!window.confirm("¿Convertir la cotización seleccionada en pedido?")) return;
      const { error: rpcError } = await supabase.rpc("convert_quotation_to_order", { p_quotation_id: selected.id });
      if (rpcError) setError(rpcError.message); else await refresh();
      return;
    }
    if (kind === "variant") {
      setAction({ title: "Nueva talla / color", fields: [
        { key: "size", label: "Talla", required: true }, { key: "color", label: "Color", required: true }, { key: "barcode", label: "Código de barras" },
      ], submit: async (values) => {
        const { error: insertError } = await supabase.from("product_variants").insert({ ...values, product_id: selected.id });
        if (insertError) throw insertError;
      } });
      return;
    }
    if (kind === "movement") {
      const variants = selected.product_variants || [];
      if (!variants.length) return setError("Este producto no tiene variantes disponibles.");
      setAction({ title: "Movimiento de inventario", fields: [
        { key: "variant_id", label: "Variante", type: "select", required: true, options: variants.map((item: any) => item.id) },
        { key: "movement_type", label: "Tipo", type: "select", required: true, options: ["entrada", "salida", "ajuste_positivo", "ajuste_negativo"] },
        { key: "quantity", label: "Cantidad", type: "number", required: true }, { key: "reason", label: "Motivo", required: true }, { key: "reference", label: "Referencia" },
      ], submit: async (values) => {
        const { error: rpcError } = await supabase.rpc("register_stock_movement", {
          p_variant_id: values.variant_id, p_movement_type: values.movement_type,
          p_quantity: values.quantity, p_reason: values.reason, p_reference: values.reference,
        });
        if (rpcError) throw rpcError;
      } });
      return;
    }
    if (kind === "status") {
      const statusField = definition.fields.find((field) => field.key === "status")!;
      setAction({ title: "Cambiar estado del pedido", fields: [statusField, { key: "notes", label: "Notas", type: "textarea" }], initial: { status: selected.status }, submit: async (values) => {
        const { error: rpcError } = await supabase.rpc("update_order_status", { p_order_id: selected.id, p_status: values.status, p_notes: values.notes });
        if (rpcError) throw rpcError;
      } });
    }
  }

  async function submitAction(values: Record<string, any>) {
    if (!action) return;
    setBusy(true); setError("");
    try { await action.submit(values); setAction(null); await refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "No se pudo completar la operación."); }
    finally { setBusy(false); }
  }

  async function exportCsv() {
    const header = definition.columns.map((column) => `"${column.label.replaceAll('"', '""')}"`).join(",");
    const lines = filtered.map((row) => definition.columns.map((column) => `"${formatValue(nested(row, column.key), column.format).replaceAll('"', '""')}"`).join(","));
    await window.desktop.saveFile({ defaultPath: `${definition.table}.csv`, filters: [{ name: "CSV", extensions: ["csv"] }], dataBase64: toBase64(`\uFEFF${[header, ...lines].join("\r\n")}`) });
  }

  const actionLabels = { movement: "Movimiento", variant: "Nueva variante", whatsapp: "WhatsApp", convert: "Convertir en pedido", status: "Cambiar estado" };
  return <section className="page-content">
    <header className="page-header"><div><h1>{definition.title}</h1><p>{rows.length} registros disponibles</p></div><div className="header-actions"><input className="search" placeholder="Buscar en resultados…" value={query} onChange={(event) => setQuery(event.target.value)} /><button className="button secondary" onClick={() => void refresh()}><RefreshCw size={16} /> Actualizar</button>{definition.allowCreate !== false && <button className="button gold" disabled={!writable} onClick={() => setModal({ mode: "create" })}><Plus size={16} /> Nuevo</button>}</div></header>
    {error && <div className="alert error">{error}</div>}
    <div className="toolbar">
      <button className="button secondary" disabled={!writable || !selected} onClick={() => selected && setModal({ mode: "edit", row: selected })}><Edit3 size={16} /> Editar</button>
      {definition.fields.some((field) => field.key === "is_active") && <button className="button danger" disabled={!writable || !selected} onClick={() => void deactivate()}><Trash2 size={16} /> Desactivar</button>}
      {definition.actions?.map((kind) => <button key={kind} className="button secondary" disabled={!writable || !selected} onClick={() => void performAction(kind)}>{kind === "whatsapp" ? <MessageCircle size={16} /> : <Settings2 size={16} />}{actionLabels[kind]}</button>)}
      <span className="spacer" /><button className="button secondary" onClick={() => void exportCsv()}><Download size={16} /> Exportar CSV</button>
    </div>
    <div className="table-card"><table><thead><tr>{definition.columns.map((column) => <th key={column.key}>{column.label}</th>)}</tr></thead><tbody>
      {loading ? <tr><td colSpan={definition.columns.length} className="table-empty">Cargando…</td></tr>
        : filtered.length === 0 ? <tr><td colSpan={definition.columns.length} className="table-empty">No hay registros para mostrar.</td></tr>
          : filtered.map((row) => <tr key={row.id} className={selectedId === row.id ? "selected" : ""} onClick={() => setSelectedId(row.id)} onDoubleClick={() => writable && setModal({ mode: "edit", row })}>{definition.columns.map((column) => <td key={column.key}>{formatValue(nested(row, column.key), column.format)}</td>)}</tr>)}
    </tbody></table></div>
    {modal && <RecordModal title={modal.mode === "create" ? `Nuevo — ${definition.title}` : `Editar — ${definition.title}`} fields={modal.mode === "create" ? definition.createFields || definition.fields : definition.fields} initial={modal.row} busy={busy} onClose={() => setModal(null)} onSave={save} />}
    {action && <RecordModal title={action.title} fields={action.fields} initial={action.initial} busy={busy} onClose={() => setAction(null)} onSave={submitAction} />}
  </section>;
}
