import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Boxes, ChevronLeft, CircleDollarSign, ClipboardList, Factory, FileBarChart, Gauge, LogOut, Menu, PackageOpen, PanelLeftClose, ReceiptText, Search, Settings as SettingsIcon, ShoppingCart, Truck, Users, UsersRound, WalletCards } from "lucide-react";
import logo from "../assets/logo.png";
import { modules } from "./data/modules";
import { can, configurationReady, loadProfile, supabase } from "./lib/supabase";
import type { Profile } from "./types";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import CrudModule from "./components/CrudModule";
import { Cash, Sales } from "./components/Sales";
import Settings, { type Preferences } from "./components/Settings";

const Reports = lazy(() => import("./components/Reports"));

const iconMap: Record<string, typeof Gauge> = {
  dashboard: Gauge, inventory: Boxes, customers: UsersRound, quotations: ClipboardList, orders: PackageOpen,
  production: Factory, sales: ShoppingCart, cash: WalletCards, suppliers: Truck, purchases: ReceiptText,
  reports: FileBarChart, users: Users, settings: SettingsIcon,
};

const nav = [
  ["dashboard", "Dashboard"], ["inventory", "Inventario"], ["customers", "Clientes / CRM"],
  ["quotations", "Cotizaciones"], ["orders", "Pedidos"], ["production", "Producción"],
  ["sales", "Punto de venta"], ["cash", "Caja"], ["suppliers", "Proveedores"],
  ["purchases", "Compras"], ["reports", "Reportes"], ["users", "Usuarios"], ["settings", "Configuración"],
] as const;

function getPreferences(): Preferences {
  try {
    const stored = JSON.parse(localStorage.getItem("cordon-preferences") || "{}");
    return { theme: stored.theme === "dark" ? "dark" : "light", compact: Boolean(stored.compact), automaticUpdates: stored.automaticUpdates !== false };
  } catch { return { theme: "light", compact: false, automaticUpdates: true }; }
}

export default function App() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState("dashboard");
  const [preferences, setPreferences] = useState(getPreferences);
  const [refreshToken, setRefreshToken] = useState(0);
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const checkedUpdates = useRef(false);

  useEffect(() => {
    if (!configurationReady) { setLoading(false); return; }
    void supabase.auth.getSession().then(async ({ data }) => {
      if (data.session?.user) {
        try { setProfile(await loadProfile(data.session.user)); } catch { await supabase.auth.signOut(); }
      }
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = preferences.theme;
    localStorage.setItem("cordon-preferences", JSON.stringify(preferences));
  }, [preferences]);

  useEffect(() => {
    if (!profile) return;
    const channel = supabase.channel("electron-desktop");
    for (const table of ["product_variants", "orders", "quotations", "embroidery_jobs", "notifications"]) {
      channel.on("postgres_changes", { event: "*", schema: "public", table }, () => setRefreshToken((value) => value + 1));
    }
    channel.subscribe();
    return () => { void supabase.removeChannel(channel); };
  }, [profile]);

  useEffect(() => {
    if (!profile || !preferences.automaticUpdates || checkedUpdates.current) return;
    checkedUpdates.current = true;
    const timer = window.setTimeout(() => void window.desktop.checkForUpdates().catch(() => undefined), 5000);
    return () => window.clearTimeout(timer);
  }, [preferences.automaticUpdates, profile]);

  const availableNav = useMemo(() => nav.filter(([id]) => id !== "users" || (profile && can(profile, "users.manage"))), [profile]);
  const definition = modules.find((item) => item.id === active);

  async function globalSearch() {
    if (search.trim().length < 2) return;
    setSearching(true);
    const { data } = await supabase.rpc("global_search", { p_query: search.trim() });
    setSearchResults(data || []); setSearching(false);
  }

  async function logout() { await supabase.auth.signOut(); setProfile(null); setActive("dashboard"); }
  if (loading) return <div className="splash"><img src={logo} alt="Cordón de Oro" /><span>Cargando sistema…</span></div>;
  if (!profile) return <Login onAuthenticated={setProfile} />;

  return <div className={`app-shell ${preferences.compact ? "compact-sidebar" : ""}`}>
    <aside className="sidebar">
      <div className="sidebar-logo"><img src={logo} alt="Cordón de Oro" /></div>
      <nav>{availableNav.map(([id, label]) => { const Icon = iconMap[id]; return <button key={id} className={active === id ? "active" : ""} onClick={() => setActive(id)} title={label}><Icon size={18} /><span>{label}</span></button>; })}</nav>
      <button className="collapse-button" onClick={() => setPreferences({ ...preferences, compact: !preferences.compact })}>{preferences.compact ? <Menu size={19} /> : <PanelLeftClose size={19} />}<span>Contraer</span></button>
    </aside>
    <div className="workspace">
      <header className="topbar">
        <div className="user-summary"><strong>{profile.fullName}</strong><span>{profile.role.replaceAll("_", " ")}</span></div>
        <div className="global-search"><Search size={17} /><input value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && void globalSearch()} placeholder="Buscar producto, cliente o pedido…" />{search && <button onClick={() => { setSearch(""); setSearchResults([]); }}><ChevronLeft size={16} /></button>}
          {(searching || searchResults.length > 0) && <div className="search-results">{searching ? <p>Buscando…</p> : searchResults.map((result) => <button key={`${result.entity}-${result.record_id}`}><strong>{result.entity}: {result.title}</strong><span>{result.subtitle}</span></button>)}</div>}
        </div>
        <button className="button primary" onClick={() => void logout()}><LogOut size={16} /> Cerrar sesión</button>
      </header>
      <main className="main-area">
        {active === "dashboard" ? <Dashboard refreshToken={refreshToken} />
          : definition ? <CrudModule definition={definition} profile={profile} refreshToken={refreshToken} />
            : active === "sales" ? <Sales />
              : active === "cash" ? <Cash />
                : active === "reports" ? <Suspense fallback={<div className="splash"><span>Cargando reportes…</span></div>}><Reports /></Suspense>
                  : <Settings profile={profile} preferences={preferences} onSave={setPreferences} />}
      </main>
      <footer className="statusbar"><span className="online-dot" /> Conectado a Supabase <span className="status-spacer" /> Electron · React · Supabase</footer>
    </div>
  </div>;
}
