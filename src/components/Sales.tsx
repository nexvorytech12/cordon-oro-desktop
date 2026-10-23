import { useMemo, useState } from "react";
import { MinusCircle, PlusCircle, ShoppingCart } from "lucide-react";
import { supabase } from "../lib/supabase";

type SaleItem = { variant_id: string; description: string; quantity: number; unit_price: number };
const money = (value: number) => new Intl.NumberFormat("es-PE", { style: "currency", currency: "PEN" }).format(value);

export function Sales() {
  const [items, setItems] = useState<SaleItem[]>([]);
  const [variant, setVariant] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [price, setPrice] = useState(0);
  const [customer, setCustomer] = useState("");
  const [cashRegister, setCashRegister] = useState("");
  const [discount, setDiscount] = useState(0);
  const [payment, setPayment] = useState(0);
  const [method, setMethod] = useState("efectivo");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const total = useMemo(() => Math.max(0, items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0) - discount), [items, discount]);

  function add() {
    if (!variant.trim()) return setError("Ingrese el ID de la variante o código del producto.");
    setItems((current) => [...current, { variant_id: variant.trim(), description: variant.trim(), quantity, unit_price: price }]);
    setVariant(""); setQuantity(1); setPrice(0); setError("");
  }

  async function checkout() {
    setError(""); setMessage("");
    if (!items.length) return setError("Agregue al menos un producto.");
    if (!cashRegister.trim()) return setError("Indique una caja abierta.");
    const { data, error: rpcError } = await supabase.rpc("register_sale", {
      p_customer_id: customer.trim() || null,
      p_cash_register_id: cashRegister.trim(),
      p_items: items,
      p_discount: discount,
      p_payment_amount: payment,
      p_payment_method: method,
      p_idempotency_key: crypto.randomUUID(),
    });
    if (rpcError) return setError(rpcError.message);
    setMessage(`Venta registrada correctamente. ID: ${data}`);
    setItems([]); setDiscount(0); setPayment(0);
  }

  return <section className="page-content">
    <header className="page-header"><div><h1>Punto de venta</h1><p>Registre ventas, pagos y movimientos de inventario en una transacción.</p></div></header>
    {error && <div className="alert error">{error}</div>}{message && <div className="alert success">{message}</div>}
    <div className="pos-layout">
      <article className="panel">
        <h2><ShoppingCart size={19} /> Productos</h2>
        <div className="inline-form">
          <label className="grow">Variante / código<input value={variant} onChange={(e) => setVariant(e.target.value)} placeholder="ID de variante" /></label>
          <label>Cantidad<input type="number" min="1" value={quantity} onChange={(e) => setQuantity(Number(e.target.value))} /></label>
          <label>Precio<input type="number" min="0" step="0.01" value={price} onChange={(e) => setPrice(Number(e.target.value))} /></label>
          <button className="button gold align-end" onClick={add}><PlusCircle size={17} /> Agregar</button>
        </div>
        <div className="table-card compact"><table><thead><tr><th>Variante</th><th>Cantidad</th><th>Precio</th><th>Importe</th><th /></tr></thead><tbody>
          {items.length === 0 ? <tr><td colSpan={5} className="table-empty">El carrito está vacío.</td></tr> : items.map((item, index) => <tr key={`${item.variant_id}-${index}`}><td>{item.description}</td><td>{item.quantity}</td><td>{money(item.unit_price)}</td><td>{money(item.quantity * item.unit_price)}</td><td><button className="icon-button danger-text" onClick={() => setItems(items.filter((_, itemIndex) => itemIndex !== index))}><MinusCircle size={18} /></button></td></tr>)}
        </tbody></table></div>
      </article>
      <article className="panel checkout-panel">
        <h2>Cobro</h2>
        <label>ID de caja abierta<input value={cashRegister} onChange={(e) => setCashRegister(e.target.value)} /></label>
        <label>ID del cliente (opcional)<input value={customer} onChange={(e) => setCustomer(e.target.value)} /></label>
        <label>Descuento<input type="number" min="0" step="0.01" value={discount} onChange={(e) => setDiscount(Number(e.target.value))} /></label>
        <label>Forma de pago<select value={method} onChange={(e) => setMethod(e.target.value)}>{["efectivo", "yape", "plin", "transferencia", "tarjeta"].map((value) => <option key={value}>{value}</option>)}</select></label>
        <label>Pago recibido<input type="number" min="0" step="0.01" value={payment} onChange={(e) => setPayment(Number(e.target.value))} /></label>
        <div className="checkout-total"><span>Total</span><strong>{money(total)}</strong></div>
        <button className="button gold wide" onClick={() => void checkout()}>COBRAR</button>
      </article>
    </div>
  </section>;
}

export function Cash() {
  const [opening, setOpening] = useState(0);
  const [registerId, setRegisterId] = useState("");
  const [counted, setCounted] = useState(0);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function openRegister() {
    const { data, error: rpcError } = await supabase.rpc("open_cash_register", { p_opening_amount: opening });
    if (rpcError) return setError(rpcError.message);
    setRegisterId(String(data)); setMessage(`Caja abierta correctamente. ID: ${data}`); setError("");
  }
  async function closeRegister() {
    if (!registerId.trim()) return setError("Indique el ID de la caja que desea cerrar.");
    const { data, error: rpcError } = await supabase.rpc("close_cash_register", { p_register_id: registerId.trim(), p_counted_amount: counted });
    if (rpcError) return setError(rpcError.message);
    setMessage(`Caja cerrada correctamente: ${JSON.stringify(data)}`); setError("");
  }
  return <section className="page-content"><header className="page-header"><div><h1>Apertura y cierre de caja</h1><p>Controle el efectivo y las diferencias de cada turno.</p></div></header>
    {error && <div className="alert error">{error}</div>}{message && <div className="alert success">{message}</div>}
    <div className="two-column"><article className="panel"><h2>Abrir caja</h2><label>Monto inicial<input type="number" min="0" step="0.01" value={opening} onChange={(e) => setOpening(Number(e.target.value))} /></label><button className="button gold" onClick={() => void openRegister()}>Abrir caja</button></article>
      <article className="panel"><h2>Cerrar caja</h2><label>ID de caja abierta<input value={registerId} onChange={(e) => setRegisterId(e.target.value)} /></label><label>Efectivo contado<input type="number" min="0" step="0.01" value={counted} onChange={(e) => setCounted(Number(e.target.value))} /></label><button className="button primary" onClick={() => void closeRegister()}>Cerrar caja</button></article></div>
  </section>;
}
