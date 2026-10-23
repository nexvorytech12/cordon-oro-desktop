-- Seguridad por filas. Ninguna autorización depende de la interfaz de escritorio.
create or replace function public.current_role_id() returns uuid
language sql stable security definer set search_path = public
as $$ select role_id from public.profiles where id = auth.uid() and is_active $$;

create or replace function public.has_permission(requested text) returns boolean
language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from public.profiles p
    join public.roles r on r.id = p.role_id
    left join public.role_permissions rp on rp.role_id = r.id
    left join public.permissions pm on pm.id = rp.permission_id
    where p.id = auth.uid() and p.is_active and (r.name = 'administrador' or pm.code = requested)
  )
$$;
revoke all on function public.current_role_id() from public;
revoke all on function public.has_permission(text) from public;
grant execute on function public.current_role_id(), public.has_permission(text) to authenticated;

alter table public.roles enable row level security;
alter table public.permissions enable row level security;
alter table public.role_permissions enable row level security;
alter table public.profiles enable row level security;
alter table public.audit_logs enable row level security;

create policy roles_read on public.roles for select to authenticated using (true);
create policy permissions_read on public.permissions for select to authenticated using (true);
create policy role_permissions_read on public.role_permissions for select to authenticated using (true);
create policy profiles_read on public.profiles for select to authenticated using (id = auth.uid() or public.has_permission('users.manage'));
create policy profiles_manage on public.profiles for all to authenticated using (public.has_permission('users.manage')) with check (public.has_permission('users.manage'));
create policy roles_manage on public.roles for all to authenticated using (public.has_permission('users.manage')) with check (public.has_permission('users.manage'));
create policy permissions_manage on public.permissions for all to authenticated using (public.has_permission('users.manage')) with check (public.has_permission('users.manage'));
create policy role_permissions_manage on public.role_permissions for all to authenticated using (public.has_permission('users.manage')) with check (public.has_permission('users.manage'));
create policy audit_read on public.audit_logs for select to authenticated using (public.has_permission('audit.read'));

-- Políticas homogéneas por dominio. RLS también se aplica a lecturas de reportes.
do $$
declare rec record;
begin
  for rec in select * from (values
    ('customers','customers.read','customers.write',true), ('customer_interactions','customers.read','customers.write',true),
    ('categories','inventory.read','inventory.write',false), ('products','inventory.read','inventory.write',true),
    ('product_variants','inventory.read','inventory.write',false), ('warehouses','inventory.read','inventory.write',false),
    ('stock_movements','inventory.read','inventory.write',true),
    ('suppliers','purchases.read','purchases.write',true), ('purchases','purchases.read','purchases.write',true),
    ('purchase_details','purchases.read','purchases.write',false),
    ('quotations','quotations.read','quotations.write',true), ('quotation_details','quotations.read','quotations.write',false),
    ('orders','orders.read','orders.write',true), ('order_details','orders.read','orders.write',false),
    ('order_status_history','orders.read','orders.write',false),
    ('production_orders','production.read','production.write',true), ('production_stages','production.read','production.write',false),
    ('embroidery_jobs','production.read','production.write',true), ('material_consumption','production.read','production.write',true),
    ('sales','sales.read','sales.write',true), ('sale_details','sales.read','sales.write',false), ('payments','sales.read','sales.write',true),
    ('cash_registers','cash.read','cash.write',false), ('cash_movements','cash.read','cash.write',true)
  ) as x(table_name, read_permission, write_permission, has_created_by)
  loop
    execute format('alter table public.%I enable row level security', rec.table_name);
    execute format('create policy %I on public.%I for select to authenticated using (public.has_permission(%L))', rec.table_name || '_read', rec.table_name, rec.read_permission);
    if rec.has_created_by then
      execute format('create policy %I on public.%I for insert to authenticated with check (public.has_permission(%L) and (created_by is null or created_by = auth.uid()))', rec.table_name || '_insert', rec.table_name, rec.write_permission);
    else
      execute format('create policy %I on public.%I for insert to authenticated with check (public.has_permission(%L))', rec.table_name || '_insert', rec.table_name, rec.write_permission);
    end if;
    execute format('create policy %I on public.%I for update to authenticated using (public.has_permission(%L)) with check (public.has_permission(%L))', rec.table_name || '_update', rec.table_name, rec.write_permission, rec.write_permission);
  end loop;
end $$;

-- Tablas sin created_by requieren políticas de inserción específicas (reemplazan las dinámicas incompatibles).
do $$ declare t text; begin
  foreach t in array array['categories','product_variants','warehouses','purchase_details','quotation_details','order_details','production_stages','sale_details','cash_registers'] loop
    execute format('drop policy %I on public.%I', t || '_insert', t);
  end loop;
end $$;
create policy categories_insert on public.categories for insert to authenticated with check(public.has_permission('inventory.write'));
create policy product_variants_insert on public.product_variants for insert to authenticated with check(public.has_permission('inventory.write'));
create policy warehouses_insert on public.warehouses for insert to authenticated with check(public.has_permission('inventory.write'));
create policy purchase_details_insert on public.purchase_details for insert to authenticated with check(public.has_permission('purchases.write'));
create policy quotation_details_insert on public.quotation_details for insert to authenticated with check(public.has_permission('quotations.write'));
create policy order_details_insert on public.order_details for insert to authenticated with check(public.has_permission('orders.write'));
create policy production_stages_insert on public.production_stages for insert to authenticated with check(public.has_permission('production.write'));
create policy sale_details_insert on public.sale_details for insert to authenticated with check(public.has_permission('sales.write'));
create policy cash_registers_insert on public.cash_registers for insert to authenticated with check(public.has_permission('cash.write') and opened_by = auth.uid());

alter table public.notifications enable row level security;
create policy notifications_read on public.notifications for select to authenticated
using (user_id = auth.uid() or role_id = public.current_role_id());
create policy notifications_update on public.notifications for update to authenticated
using (user_id = auth.uid() or role_id = public.current_role_id()) with check (is_read = true);

-- Auditoría inmutable para cambios de datos sensibles.
create or replace function public.audit_row() returns trigger
language plpgsql security definer set search_path = public as $$
declare rid text;
begin
  rid := coalesce((case when tg_op = 'DELETE' then to_jsonb(old) else to_jsonb(new) end)->>'id', '');
  insert into public.audit_logs(user_id, table_name, record_id, action, old_data, new_data)
  values(auth.uid(), tg_table_name, rid, tg_op, case when tg_op <> 'INSERT' then to_jsonb(old) end, case when tg_op <> 'DELETE' then to_jsonb(new) end);
  return case when tg_op = 'DELETE' then old else new end;
end $$;
do $$ declare t text; begin
  foreach t in array array['profiles','products','product_variants','stock_movements','customers','quotations','orders','production_orders','embroidery_jobs','purchases','sales','payments','cash_registers'] loop
    execute format('create trigger audit_%I after insert or update or delete on public.%I for each row execute function public.audit_row()', t, t);
  end loop;
end $$;

grant usage on schema public to authenticated;
grant select, insert, update on all tables in schema public to authenticated;
grant usage, select on all sequences in schema public to authenticated;
revoke delete on all tables in schema public from authenticated;

