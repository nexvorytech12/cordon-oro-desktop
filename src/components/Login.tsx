import { useState, type FormEvent } from "react";
import { Eye, EyeOff, LockKeyhole } from "lucide-react";
import logo from "../../assets/logo.png";
import { configurationReady, loadProfile, supabase } from "../lib/supabase";
import type { Profile } from "../types";

export default function Login({ onAuthenticated }: { onAuthenticated: (profile: Profile) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!configurationReady) return setError("La configuración pública de Supabase no está disponible.");
    setBusy(true);
    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({ email, password });
      if (authError) throw authError;
      if (!data.user) throw new Error("Supabase no devolvió un usuario válido.");
      onAuthenticated(await loadProfile(data.user));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo iniciar sesión.");
      await supabase.auth.signOut();
    } finally {
      setBusy(false);
    }
  }

  async function resetPassword() {
    setError("");
    if (!email.trim()) return setError("Escriba primero su correo electrónico.");
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email.trim());
    if (resetError) setError(resetError.message);
    else setMessage("Revise su correo para continuar la recuperación.");
  }

  return (
    <main className="login-page">
      <section className="login-brand">
        <div className="logo-box"><img src={logo} alt="Cordón de Oro E.I.R.L." /></div>
        <h1>Gestión empresarial</h1>
        <p>Confección, bordado industrial y comercialización en un solo sistema.</p>
        <span><LockKeyhole size={16} /> Sesión protegida por Supabase Auth</span>
      </section>
      <section className="login-panel">
        <form className="login-form" onSubmit={submit}>
          <p className="eyebrow">CORDÓN DE ORO E.I.R.L.</p>
          <h2>Bienvenido</h2>
          <p className="muted">Ingrese con su cuenta empresarial</p>
          <label>Correo electrónico<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="usuario@cordondeoro.pe" required /></label>
          <label>Contraseña
            <span className="password-field">
              <input type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required />
              <button type="button" className="icon-button" onClick={() => setShowPassword((value) => !value)} aria-label="Mostrar contraseña">
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </span>
          </label>
          {error && <div className="alert error">{error}</div>}
          {message && <div className="alert success">{message}</div>}
          <button className="button gold wide" disabled={busy}>{busy ? "CONECTANDO…" : "INICIAR SESIÓN"}</button>
          <button type="button" className="link-button" onClick={resetPassword}>Olvidé mi contraseña</button>
        </form>
      </section>
    </main>
  );
}
