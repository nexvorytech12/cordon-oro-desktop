-- Cordón de Oro E.I.R.L. — Esquema inicial
-- Ejecutar mediante Supabase CLI: supabase db push
create extension if not exists pgcrypto;
create extension if not exists btree_gist;

create sequence if not exists quotation_number_seq start 1;
create sequence if not exists order_number_seq start 1;
create sequence if not exists sale_number_seq start 1;
create sequence if not exists purchase_number_seq start 1;
create sequence if not exists embroidery_number_seq start 1;

create table public.roles (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  description text,
  created_at timestamptz not null default now()
);
create table public.permissions (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  description text not null,
  created_at timestamptz not null default now()
);
create table public.role_permissions (
  role_id uuid not null references public.roles(id) on delete cascade,
  permission_id uuid not null references public.permissions(id) on delete cascade,
  primary key (role_id, permission_id)
);
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  role_id uuid references public.roles(id),
  full_name text not null,
  phone text,
  is_active boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table public.audit_logs (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users(id) on delete set null,
  table_name text not null,
  record_id text,
  action text not null check (action in ('INSERT','UPDATE','DELETE','RPC')),
  old_data jsonb,
  new_data jsonb,
  occurred_at timestamptz not null default now()
);

create table public.customers (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  document_type text not null default 'DNI',
  document_number text,
  phone text, whatsapp text, email text, address text,
  customer_type text not null default 'persona' check (customer_type in ('persona','empresa','institución')),
  notes text, is_active boolean not null default true,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  created_by uuid references auth.users(id) default auth.uid(),
  constraint customers_document_unique unique nulls not distinct (document_type, document_number)
);
create table public.customer_interactions (
  id uuid primary key default gen_random_uuid(), customer_id uuid not null references public.customers(id),
  interaction_type text not null, subject text not null, notes text,
  status text not null default 'nuevo' check (status in ('nuevo','en_atención','cotizado','pendiente_respuesta','confirmado','cerrado')),
  responsible_id uuid references public.profiles(id), reminder_at timestamptz,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);

create table public.categories (
  id uuid primary key default gen_random_uuid(), name text not null unique, description text,
  is_active boolean not null default true, created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.suppliers (
  id uuid primary key default gen_random_uuid(), ruc text unique, name text not null,
  contact_name text, phone text, email text, address text, notes text, is_active boolean not null default true,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.products (
  id uuid primary key default gen_random_uuid(), sku text not null unique, name text not null,
  product_type text not null check (product_type in ('terminado','materia_prima')),
  category_id uuid references public.categories(id), description text,
  unit text not null, cost numeric(14,2) not null default 0 check (cost >= 0),
  price numeric(14,2) not null default 0 check (price >= 0), minimum_stock numeric(14,3) not null default 0,
  supplier_id uuid references public.suppliers(id), image_path text, is_active boolean not null default true,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.product_variants (
  id uuid primary key default gen_random_uuid(), product_id uuid not null references public.products(id),
  size text not null default 'Única', color text not null default 'Sin color', barcode text unique,
  stock numeric(14,3) not null default 0 check (stock >= 0), is_active boolean not null default true,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  unique(product_id, size, color)
);
create or replace function public.create_default_variant() returns trigger language plpgsql as $$
begin
  insert into public.product_variants(product_id) values(new.id);
  return new;
end $$;
create trigger product_default_variant after insert on public.products for each row execute function public.create_default_variant();
create table public.warehouses (
  id uuid primary key default gen_random_uuid(), name text not null unique, address text, is_active boolean not null default true,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table public.stock_movements (
  id uuid primary key default gen_random_uuid(), variant_id uuid not null references public.product_variants(id),
  warehouse_id uuid references public.warehouses(id), movement_type text not null check (movement_type in ('entrada','salida','ajuste_positivo','ajuste_negativo')),
  quantity numeric(14,3) not null check (quantity > 0), balance_after numeric(14,3) not null,
  reason text not null, reference text, idempotency_key uuid unique,
  created_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);

create table public.purchases (
  id uuid primary key default gen_random_uuid(), number text not null unique default ('OC-' || to_char(now(),'YYYY') || '-' || lpad(nextval('purchase_number_seq')::text,6,'0')),
  supplier_id uuid not null references public.suppliers(id), status text not null default 'borrador' check(status in ('borrador','ordenada','recibida','cancelada')),
  purchase_date date not null default current_date, subtotal numeric(14,2) not null default 0, tax numeric(14,2) not null default 0,
  total numeric(14,2) not null default 0, paid numeric(14,2) not null default 0, notes text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.purchase_details (
  id uuid primary key default gen_random_uuid(), purchase_id uuid not null references public.purchases(id) on delete cascade,
  variant_id uuid not null references public.product_variants(id), quantity numeric(14,3) not null check(quantity > 0),
  received_quantity numeric(14,3) not null default 0, unit_cost numeric(14,2) not null check(unit_cost >= 0), total numeric(14,2) generated always as (quantity * unit_cost) stored
);

create table public.quotations (
  id uuid primary key default gen_random_uuid(), number text not null unique default ('COT-' || to_char(now(),'YYYY') || '-' || lpad(nextval('quotation_number_seq')::text,6,'0')),
  customer_id uuid not null references public.customers(id), status text not null default 'borrador' check(status in ('borrador','enviada','aprobada','rechazada','vencida')),
  issue_date date not null default current_date, valid_until date, subtotal numeric(14,2) not null default 0,
  discount numeric(14,2) not null default 0, tax numeric(14,2) not null default 0, total numeric(14,2) not null default 0,
  estimated_delivery date, reference_path text, pdf_path text, notes text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.quotation_details (
  id uuid primary key default gen_random_uuid(), quotation_id uuid not null references public.quotations(id) on delete cascade,
  garment_type text not null, service text not null, description text, quantity numeric(14,3) not null check(quantity > 0),
  sizes text, colors text, material text, unit_price numeric(14,2) not null, discount numeric(14,2) not null default 0,
  total numeric(14,2) generated always as ((quantity * unit_price) - discount) stored
);

create table public.orders (
  id uuid primary key default gen_random_uuid(), number text not null unique default ('PED-' || to_char(now(),'YYYY') || '-' || lpad(nextval('order_number_seq')::text,6,'0')),
  quotation_id uuid unique references public.quotations(id), customer_id uuid not null references public.customers(id),
  status text not null default 'registrado', order_date date not null default current_date, delivery_date date,
  responsible_id uuid references public.profiles(id), total numeric(14,2) not null default 0, advance numeric(14,2) not null default 0,
  balance numeric(14,2) not null default 0, notes text, is_active boolean not null default true,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.order_details (
  id uuid primary key default gen_random_uuid(), order_id uuid not null references public.orders(id) on delete cascade,
  product_id uuid references public.products(id), description text not null, quantity numeric(14,3) not null check(quantity > 0),
  sizes text, colors text, unit_price numeric(14,2) not null default 0, total numeric(14,2) generated always as (quantity * unit_price) stored
);
create table public.order_status_history (
  id uuid primary key default gen_random_uuid(), order_id uuid not null references public.orders(id) on delete cascade,
  from_status text, to_status text not null, notes text, changed_at timestamptz not null default now(), changed_by uuid references auth.users(id) default auth.uid()
);

create table public.production_orders (
  id uuid primary key default gen_random_uuid(), order_id uuid not null references public.orders(id), status text not null default 'pendiente',
  planned_start timestamptz, planned_end timestamptz, actual_start timestamptz, actual_end timestamptz,
  responsible_id uuid references public.profiles(id), notes text,
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.production_stages (
  id uuid primary key default gen_random_uuid(), production_order_id uuid not null references public.production_orders(id) on delete cascade,
  stage text not null, sequence integer not null, status text not null default 'pendiente', operator_id uuid references public.profiles(id),
  started_at timestamptz, finished_at timestamptz, notes text, unique(production_order_id, sequence)
);
create table public.embroidery_jobs (
  id uuid primary key default gen_random_uuid(), number text not null unique default ('BOR-' || to_char(now(),'YYYY') || '-' || lpad(nextval('embroidery_number_seq')::text,6,'0')),
  order_id uuid references public.orders(id), customer_id uuid references public.customers(id), design_path text,
  garment_type text not null, quantity integer not null check(quantity > 0), thread_colors text, stitch_count integer not null default 0,
  operator_id uuid references public.profiles(id), start_date date, end_date date, estimated_minutes integer, actual_minutes integer,
  approved_pieces integer not null default 0, defective_pieces integer not null default 0,
  status text not null default 'pendiente' check(status in ('pendiente','programado','en_proceso','pausado','terminado','cancelado')),
  created_at timestamptz not null default now(), updated_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.material_consumption (
  id uuid primary key default gen_random_uuid(), production_order_id uuid references public.production_orders(id), embroidery_job_id uuid references public.embroidery_jobs(id),
  variant_id uuid not null references public.product_variants(id), planned_quantity numeric(14,3) not null default 0,
  actual_quantity numeric(14,3) not null default 0, created_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid(),
  check (production_order_id is not null or embroidery_job_id is not null)
);

create table public.cash_registers (
  id uuid primary key default gen_random_uuid(), opened_by uuid not null references public.profiles(id), opened_at timestamptz not null default now(),
  opening_amount numeric(14,2) not null default 0, closed_by uuid references public.profiles(id), closed_at timestamptz,
  expected_amount numeric(14,2), counted_amount numeric(14,2), difference numeric(14,2), status text not null default 'abierta' check(status in ('abierta','cerrada')),
  notes text, constraint one_open_register_per_user exclude using gist (opened_by with =) where (status = 'abierta')
);
create table public.sales (
  id uuid primary key default gen_random_uuid(), number text not null unique default ('V-' || to_char(now(),'YYYY') || '-' || lpad(nextval('sale_number_seq')::text,7,'0')),
  customer_id uuid references public.customers(id), order_id uuid references public.orders(id), cash_register_id uuid not null references public.cash_registers(id),
  sale_date timestamptz not null default now(), subtotal numeric(14,2) not null, discount numeric(14,2) not null default 0,
  total numeric(14,2) not null, paid numeric(14,2) not null default 0, balance numeric(14,2) not null default 0,
  status text not null default 'confirmada' check(status in ('confirmada','anulada')), annulled_by uuid references public.profiles(id), annulled_at timestamptz,
  idempotency_key uuid not null unique,
  created_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.sale_details (
  id uuid primary key default gen_random_uuid(), sale_id uuid not null references public.sales(id) on delete cascade,
  variant_id uuid not null references public.product_variants(id), quantity numeric(14,3) not null check(quantity > 0),
  unit_price numeric(14,2) not null, total numeric(14,2) generated always as (quantity * unit_price) stored
);
create table public.payments (
  id uuid primary key default gen_random_uuid(), sale_id uuid references public.sales(id), order_id uuid references public.orders(id),
  amount numeric(14,2) not null check(amount > 0), method text not null check(method in ('efectivo','yape','plin','transferencia','tarjeta')),
  reference text, paid_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid(),
  check(sale_id is not null or order_id is not null)
);
create table public.cash_movements (
  id uuid primary key default gen_random_uuid(), cash_register_id uuid not null references public.cash_registers(id),
  movement_type text not null check(movement_type in ('ingreso','egreso')), amount numeric(14,2) not null check(amount > 0),
  reason text not null, payment_id uuid references public.payments(id), created_at timestamptz not null default now(), created_by uuid references auth.users(id) default auth.uid()
);
create table public.notifications (
  id uuid primary key default gen_random_uuid(), user_id uuid references public.profiles(id), role_id uuid references public.roles(id),
  title text not null, body text not null, entity_type text, entity_id uuid, is_read boolean not null default false,
  created_at timestamptz not null default now()
);

create index customers_name_idx on public.customers using gin (to_tsvector('spanish', name));
create index products_name_idx on public.products using gin (to_tsvector('spanish', name));
create index stock_movements_variant_date_idx on public.stock_movements(variant_id, created_at desc);
create index orders_status_delivery_idx on public.orders(status, delivery_date);
create index sales_date_idx on public.sales(sale_date desc);
create index interactions_reminder_idx on public.customer_interactions(reminder_at) where reminder_at is not null;

create or replace function public.set_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;
do $$ declare t text; begin
  foreach t in array array['profiles','customers','customer_interactions','categories','suppliers','products','product_variants','purchases','quotations','orders','production_orders','embroidery_jobs'] loop
    execute format('create trigger set_updated_at before update on public.%I for each row execute function public.set_updated_at()', t);
  end loop;
end $$;

create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles(id, full_name, is_active) values(new.id, coalesce(new.raw_user_meta_data->>'full_name', new.email, 'Usuario'), false);
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users for each row execute function public.handle_new_user();

