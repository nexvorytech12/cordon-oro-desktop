import { useState } from "react";
import { FileDown, FileSpreadsheet } from "lucide-react";
import ExcelJS from "exceljs";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { supabase } from "../lib/supabase";

const reports = {
  "Inventario actual": ["inventory_report", [["sku", "SKU"], ["name", "Producto"], ["size", "Talla"], ["color", "Color"], ["stock", "Stock"], ["value", "Valor"]]],
  Kardex: ["kardex_report", [["created_at", "Fecha"], ["sku", "SKU"], ["movement_type", "Tipo"], ["quantity", "Cantidad"], ["balance", "Saldo"], ["reason", "Motivo"]]],
  Ventas: ["sales_report", [["sale_date", "Fecha"], ["number", "Venta"], ["customer", "Cliente"], ["total", "Total"], ["paid", "Pagado"], ["balance", "Saldo"]]],
  "Pedidos pendientes": ["pending_orders_report", [["number", "Pedido"], ["customer", "Cliente"], ["status", "Estado"], ["delivery_date", "Entrega"], ["balance", "Saldo"]]],
  Producción: ["production_report", [["number", "Orden"], ["operator", "Operador"], ["status", "Estado"], ["quantity", "Cantidad"], ["approved", "Aprobadas"], ["defective", "Defectuosas"]]],
  Compras: ["purchases_report", [["purchase_date", "Fecha"], ["number", "Compra"], ["supplier", "Proveedor"], ["total", "Total"], ["paid", "Pagado"]]],
} as const;

function base64(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer); let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary);
}

export default function Reports() {
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  async function generate(name: keyof typeof reports, kind: "xlsx" | "pdf") {
    setBusy(`${name}-${kind}`); setError("");
    const [rpc, columns] = reports[name];
    const { data, error: rpcError } = await supabase.rpc(rpc);
    if (rpcError) { setError(rpcError.message); setBusy(""); return; }
    const rows = (data || []) as Record<string, any>[];
    if (kind === "xlsx") {
      const workbook = new ExcelJS.Workbook();
      const sheet = workbook.addWorksheet(name.slice(0, 31));
      sheet.addRow(columns.map(([, label]) => label));
      rows.forEach((row) => sheet.addRow(columns.map(([key]) => row[key] ?? "")));
      sheet.getRow(1).eachCell((cell) => {
        cell.font = { bold: true, color: { argb: "FFFFFFFF" } };
        cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FF0B1F35" } };
      });
      sheet.columns.forEach((column) => { column.width = 18; });
      sheet.views = [{ state: "frozen", ySplit: 1 }];
      const output = await workbook.xlsx.writeBuffer();
      await window.desktop.saveFile({ defaultPath: `${name.replaceAll(" ", "_")}.xlsx`, filters: [{ name: "Excel", extensions: ["xlsx"] }], dataBase64: base64(output) });
    } else {
      const document = new jsPDF({ orientation: "landscape" });
      document.setFontSize(16); document.text(`CORDÓN DE ORO E.I.R.L. — ${name}`, 14, 16);
      document.setFontSize(9); document.text(`Generado: ${new Date().toLocaleString("es-PE")}`, 14, 23);
      autoTable(document, { startY: 29, head: [columns.map(([, label]) => label)], body: rows.map((row) => columns.map(([key]) => String(row[key] ?? ""))), headStyles: { fillColor: [11, 31, 53] }, styles: { fontSize: 7 } });
      await window.desktop.saveFile({ defaultPath: `${name.replaceAll(" ", "_")}.pdf`, filters: [{ name: "PDF", extensions: ["pdf"] }], dataBase64: document.output("datauristring").split(",")[1] });
    }
    setBusy("");
  }
  return <section className="page-content"><header className="page-header"><div><h1>Centro de reportes</h1><p>Exporte información autorizada por RLS a Excel o PDF.</p></div></header>{error && <div className="alert error">{error}</div>}<div className="report-grid">{(Object.keys(reports) as Array<keyof typeof reports>).map((name) => <article className="report-card" key={name}><h2>{name}</h2><p>Información actualizada directamente desde Supabase.</p><div><button className="button secondary" disabled={Boolean(busy)} onClick={() => void generate(name, "xlsx")}><FileSpreadsheet size={17} /> Excel</button><button className="button primary" disabled={Boolean(busy)} onClick={() => void generate(name, "pdf")}><FileDown size={17} /> PDF</button></div></article>)}</div></section>;
}
