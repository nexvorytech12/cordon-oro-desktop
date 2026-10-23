import type { FieldDefinition, ModuleDefinition } from "../types";

const active: FieldDefinition = { key: "is_active", label: "Activo", type: "boolean" };
const notes: FieldDefinition = { key: "notes", label: "Observaciones", type: "textarea" };

export const modules: ModuleDefinition[] = [
  {
    id: "inventory", title: "Inventario", table: "products", permission: "inventory.write",
    select: "id,sku,name,product_type,unit,cost,price,minimum_stock,is_active,created_at,product_variants(id,stock,size,color,barcode)",
    columns: [
      { key: "sku", label: "SKU" }, { key: "name", label: "Producto" },
      { key: "product_type", label: "Tipo" }, { key: "unit", label: "Unidad" },
      { key: "price", label: "Precio", format: "money" }, { key: "minimum_stock", label: "Mínimo" },
      { key: "is_active", label: "Activo", format: "boolean" },
    ],
    fields: [
      { key: "sku", label: "SKU", required: true }, { key: "name", label: "Nombre", required: true },
      { key: "product_type", label: "Tipo", type: "select", required: true, options: ["terminado", "materia_prima"] },
      { key: "category_id", label: "ID de categoría" }, { key: "description", label: "Descripción", type: "textarea" },
      { key: "unit", label: "Unidad", type: "select", required: true, options: ["unidad", "metro", "kilo", "cono", "rollo", "docena"] },
      { key: "cost", label: "Costo", type: "number" }, { key: "price", label: "Precio", type: "number" },
      { key: "minimum_stock", label: "Stock mínimo", type: "number" }, { key: "supplier_id", label: "ID de proveedor" }, active,
    ], actions: ["movement", "variant"],
  },
  {
    id: "customers", title: "Clientes / CRM", table: "customers", permission: "customers.write",
    columns: [
      { key: "document_number", label: "DNI/RUC" }, { key: "name", label: "Cliente" },
      { key: "phone", label: "Teléfono" }, { key: "email", label: "Correo" },
      { key: "customer_type", label: "Tipo" }, { key: "is_active", label: "Activo", format: "boolean" },
    ],
    fields: [
      { key: "name", label: "Nombre / razón social", required: true },
      { key: "document_type", label: "Documento", type: "select", required: true, options: ["DNI", "RUC", "CE", "Otro"] },
      { key: "document_number", label: "Número" }, { key: "phone", label: "Teléfono" },
      { key: "whatsapp", label: "WhatsApp" }, { key: "email", label: "Correo" },
      { key: "address", label: "Dirección" },
      { key: "customer_type", label: "Tipo", type: "select", required: true, options: ["persona", "empresa", "institución"] },
      notes, active,
    ], actions: ["whatsapp"],
  },
  {
    id: "quotations", title: "Cotizaciones", table: "quotations", permission: "quotations.write",
    columns: [
      { key: "number", label: "Número" }, { key: "customer_id", label: "Cliente ID" },
      { key: "status", label: "Estado" }, { key: "issue_date", label: "Fecha", format: "date" },
      { key: "total", label: "Total", format: "money" }, { key: "estimated_delivery", label: "Entrega", format: "date" },
    ],
    fields: [
      { key: "customer_id", label: "ID del cliente", required: true },
      { key: "status", label: "Estado", type: "select", required: true, options: ["borrador", "enviada", "aprobada", "rechazada", "vencida"] },
      { key: "issue_date", label: "Fecha", type: "date", required: true }, { key: "valid_until", label: "Válida hasta", type: "date" },
      { key: "subtotal", label: "Subtotal", type: "number" }, { key: "discount", label: "Descuento", type: "number" },
      { key: "tax", label: "Impuesto", type: "number" }, { key: "total", label: "Total", type: "number" },
      { key: "estimated_delivery", label: "Entrega estimada", type: "date" }, notes,
    ], actions: ["convert"],
  },
  {
    id: "orders", title: "Pedidos", table: "orders", permission: "orders.write",
    columns: [
      { key: "number", label: "Pedido" }, { key: "customer_id", label: "Cliente ID" },
      { key: "status", label: "Estado" }, { key: "order_date", label: "Fecha", format: "date" },
      { key: "delivery_date", label: "Entrega", format: "date" }, { key: "total", label: "Total", format: "money" },
      { key: "balance", label: "Saldo", format: "money" },
    ],
    fields: [
      { key: "customer_id", label: "ID del cliente", required: true },
      { key: "status", label: "Estado", type: "select", required: true, options: ["registrado", "diseño_pendiente", "diseño_aprobado", "materiales_preparados", "corte", "confección", "bordado", "estampado", "control_calidad", "listo_entrega", "entregado", "cancelado"] },
      { key: "order_date", label: "Fecha", type: "date", required: true }, { key: "delivery_date", label: "Entrega", type: "date" },
      { key: "responsible_id", label: "ID responsable" }, { key: "total", label: "Total", type: "number" },
      { key: "advance", label: "Adelanto", type: "number" }, { key: "balance", label: "Saldo", type: "number" }, notes,
    ], actions: ["status"],
  },
  {
    id: "production", title: "Producción y bordado", table: "embroidery_jobs", permission: "production.write",
    columns: [
      { key: "number", label: "Orden" }, { key: "garment_type", label: "Prenda" }, { key: "quantity", label: "Cantidad" },
      { key: "stitch_count", label: "Puntadas" }, { key: "status", label: "Estado" },
      { key: "approved_pieces", label: "Aprobadas" }, { key: "defective_pieces", label: "Defectuosas" },
    ],
    fields: [
      { key: "customer_id", label: "ID cliente" }, { key: "order_id", label: "ID pedido" },
      { key: "design_path", label: "Diseño / ruta" }, { key: "garment_type", label: "Tipo de prenda", required: true },
      { key: "quantity", label: "Cantidad", type: "number", required: true }, { key: "thread_colors", label: "Colores de hilo" },
      { key: "stitch_count", label: "Puntadas", type: "number" }, { key: "operator_id", label: "ID operador" },
      { key: "start_date", label: "Inicio", type: "date" }, { key: "end_date", label: "Finalización", type: "date" },
      { key: "estimated_minutes", label: "Minutos estimados", type: "number" }, { key: "actual_minutes", label: "Minutos reales", type: "number" },
      { key: "approved_pieces", label: "Piezas aprobadas", type: "number" }, { key: "defective_pieces", label: "Piezas defectuosas", type: "number" },
      { key: "status", label: "Estado", type: "select", required: true, options: ["pendiente", "programado", "en_proceso", "pausado", "terminado", "cancelado"] },
    ],
  },
  {
    id: "suppliers", title: "Proveedores", table: "suppliers", permission: "purchases.write",
    columns: [
      { key: "ruc", label: "RUC" }, { key: "name", label: "Proveedor" }, { key: "contact_name", label: "Contacto" },
      { key: "phone", label: "Teléfono" }, { key: "email", label: "Correo" }, { key: "is_active", label: "Activo", format: "boolean" },
    ],
    fields: [
      { key: "ruc", label: "RUC" }, { key: "name", label: "Razón social", required: true },
      { key: "contact_name", label: "Contacto" }, { key: "phone", label: "Teléfono" },
      { key: "email", label: "Correo" }, { key: "address", label: "Dirección" }, notes, active,
    ],
  },
  {
    id: "purchases", title: "Compras", table: "purchases", permission: "purchases.write",
    columns: [
      { key: "number", label: "Compra" }, { key: "supplier_id", label: "Proveedor ID" },
      { key: "status", label: "Estado" }, { key: "purchase_date", label: "Fecha", format: "date" },
      { key: "total", label: "Total", format: "money" }, { key: "paid", label: "Pagado", format: "money" },
    ],
    fields: [
      { key: "supplier_id", label: "ID proveedor", required: true },
      { key: "status", label: "Estado", type: "select", required: true, options: ["borrador", "ordenada", "recibida", "cancelada"] },
      { key: "purchase_date", label: "Fecha", type: "date", required: true },
      { key: "subtotal", label: "Subtotal", type: "number" }, { key: "tax", label: "Impuesto", type: "number" },
      { key: "total", label: "Total", type: "number" }, { key: "paid", label: "Pagado", type: "number" }, notes,
    ],
  },
  {
    id: "users", title: "Usuarios", table: "profiles", permission: "users.manage",
    select: "id,full_name,phone,is_active,role_id,roles(name),created_at",
    columns: [
      { key: "full_name", label: "Nombre" }, { key: "phone", label: "Teléfono" },
      { key: "roles.name", label: "Rol" }, { key: "is_active", label: "Activo", format: "boolean" },
      { key: "created_at", label: "Creado", format: "date" },
    ],
    fields: [
      { key: "full_name", label: "Nombre completo", required: true }, { key: "phone", label: "Teléfono" },
      { key: "role_id", label: "ID del rol", required: true }, active,
    ],
    createFields: [
      { key: "email", label: "Correo", required: true },
      { key: "password", label: "Contraseña temporal (mínimo 10 caracteres)", type: "password", required: true },
      { key: "full_name", label: "Nombre completo", required: true },
      { key: "role_id", label: "ID del rol", required: true },
    ],
  },
];
