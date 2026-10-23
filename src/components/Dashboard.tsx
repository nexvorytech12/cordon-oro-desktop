import { useCallback, useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, Boxes, CircleDollarSign, ClipboardList, PackageCheck, Shirt, UsersRound, WalletCards } from "lucide-react";
import { supabase } from "../lib/supabase";

type Metrics = Record<string, number>;
type Point = { day: string; total: number };

const cards = [
  ["products", "Productos", Shirt], ["total_stock", "Stock total", Boxes],
  ["low_stock", "Stock bajo", AlertTriangle], ["active_customers", "Clientes activos", UsersRound],
  ["pending_quotes", "Cotizaciones pendientes", ClipboardList], ["production_orders", "En producción", PackageCheck],
  ["delivered_orders", "Entregados", PackageCheck], ["daily_sales", "Ventas de hoy", WalletCards],
  ["monthly_sales", "Ventas del mes", CircleDollarSign], ["total_income", "Ingresos acumulados", CircleDollarSign],
] as const;

const moneyKeys = new Set(["daily_sales", "monthly_sales", "total_income"]);
const money = (value: number) => new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN" }).format(value || 0);
const shortMoney = (value: number) => value >= 1000 ? `S/ ${(value / 1000).toFixed(1)} mil` : `S/ ${value.toFixed(0)}`;

export default function Dashboard({ refreshToken }: { refreshToken: number }) {
  const [metrics, setMetrics] = useState<Metrics>({});
  const [points, setPoints] = useState<Point[]>([]);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    const [metricResult, salesResult] = await Promise.all([
      supabase.rpc("dashboard_metrics"),
      supabase.rpc("sales_last_30_days"),
    ]);
    if (metricResult.error) return setError(metricResult.error.message);
    if (salesResult.error) return setError(salesResult.error.message);
    const raw = Array.isArray(metricResult.data) ? metricResult.data[0] : metricResult.data;
    setMetrics(raw ?? {});
    setPoints((salesResult.data ?? []).map((item: any) => ({ day: String(item.day), total: Number(item.total || 0) })));
    setError("");
  }, []);

  useEffect(() => { void refresh(); }, [refresh, refreshToken]);
  useEffect(() => {
    const timer = window.setInterval(() => void refresh(), 60_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const hasSales = points.some((point) => point.total > 0);
  return (
    <section className="page-content">
      <header className="page-header"><div><h1>Resumen empresarial</h1><p>Indicadores actualizados desde Supabase</p></div><button className="button secondary" onClick={() => void refresh()}>Actualizar</button></header>
      {error && <div className="alert error">{error}</div>}
      <div className="metric-grid">
        {cards.map(([key, label, Icon]) => <article className="metric-card" key={key}><span className="metric-icon"><Icon size={20} /></span><div><p>{label}</p><strong>{moneyKeys.has(key) ? money(metrics[key]) : Number(metrics[key] || 0).toLocaleString("es-PE")}</strong></div></article>)}
      </div>
      <article className="chart-card">
        <div className="chart-heading"><div><h2>Ventas de los últimos 30 días</h2><p>Evolución diaria de ingresos confirmados</p></div><span className="legend"><i /> Ventas</span></div>
        <div className="chart-wrap">
          {hasSales ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={points} margin={{ top: 16, right: 18, left: 12, bottom: 4 }}>
                <defs><linearGradient id="salesFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#C5A052" stopOpacity={0.32} /><stop offset="100%" stopColor="#C5A052" stopOpacity={0.03} /></linearGradient></defs>
                <CartesianGrid stroke="#E8EDF2" vertical={false} />
                <XAxis dataKey="day" tickFormatter={(value) => value.slice(8, 10) + "/" + value.slice(5, 7)} tick={{ fill: "#64748B", fontSize: 12 }} axisLine={{ stroke: "#CBD5E1" }} tickLine={false} minTickGap={30} />
                <YAxis tickFormatter={shortMoney} tick={{ fill: "#64748B", fontSize: 12 }} axisLine={false} tickLine={false} width={74} />
                <Tooltip formatter={(value) => [money(Number(value)), "Ventas"]} labelFormatter={(value) => `Fecha: ${String(value).slice(8, 10)}/${String(value).slice(5, 7)}`} contentStyle={{ borderRadius: 10, border: "1px solid #E2E7EC" }} />
                <Area type="monotone" dataKey="total" stroke="#B78D35" strokeWidth={3} fill="url(#salesFill)" dot={{ r: 3, fill: "#C5A052", stroke: "white", strokeWidth: 1 }} activeDot={{ r: 5 }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <div className="empty-chart"><CircleDollarSign size={34} /><strong>Aún no hay ventas registradas</strong><span>El gráfico se actualizará al confirmar la primera venta.</span></div>}
        </div>
      </article>
    </section>
  );
}
