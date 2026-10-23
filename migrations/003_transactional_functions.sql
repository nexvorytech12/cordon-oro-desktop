-- RPC transaccionales: bloqueos de fila y validaciones en servidor.
create or replace function public.register_stock_movement(
  p_variant_id uuid, p_movement_type text, p_quantity numeric, p_reason text,
  p_reference text default null, p_warehouse_id uuid default null, p_idempotency_key uuid default gen_random_uuid()
) returns uuid language plpgsql security definer set search_path = public as $$
declare v_stock numeric; v_new numeric; v_id uuid;
begin
  if not public.has_permission('inventory.write') then raise exception 'No autorizado'; end if;
  if p_quantity <= 0 then raise exception 'La cantidad debe ser positiva'; end if;
  if p_movement_type not in ('entrada','salida','ajuste_positivo','ajuste_negativo') then raise exception 'Tipo de movimiento inválido'; end if;
  select stock into v_stock from public.product_variants where id = p_variant_id and is_active for update;
  if not found then raise exception 'Variante no encontrada o inactiva'; end if;
  v_new := case when p_movement_type in ('entrada','ajuste_positivo') then v_stock + p_quantity else v_stock - p_quantity end;
  if v_new < 0 then raise exception 'Stock insuficiente. Disponible: %', v_stock; end if;
  insert into public.stock_movements(variant_id, warehouse_id, movement_type, quantity, balance_after, reason, reference, idempotency_key, created_by)
  values(p_variant_id, p_warehouse_id, p_movement_type, p_quantity, v_new, p_reason, p_reference, p_idempotency_key, auth.uid()) returning id into v_id;
  update public.product_variants set stock = v_new, updated_at = now() where id = p_variant_id;
  return v_id;
exception when unique_violation then
  select id into v_id from public.stock_movements where idempotency_key = p_idempotency_key;
  return v_id;
end $$;

create or replace function public.open_cash_register(p_opening_amount numeric) returns uuid
language plpgsql security definer set search_path = public as $$
declare v_id uuid;
begin
  if not public.has_permission('cash.write') then raise exception 'No autorizado'; end if;
  if p_opening_amount < 0 then raise exception 'Monto inicial inválido'; end if;
  insert into public.cash_registers(opened_by, opening_amount) values(auth.uid(), p_opening_amount) returning id into v_id;
  return v_id;
end $$;

create or replace function public.close_cash_register(p_register_id uuid, p_counted_amount numeric) returns jsonb
language plpgsql security definer set search_path = public as $$
declare v_expected numeric; v_opened_by uuid;
begin
  if not public.has_permission('cash.write') then raise exception 'No autorizado'; end if;
  select opened_by into v_opened_by from public.cash_registers where id=p_register_id and status='abierta' for update;
  if not found then raise exception 'Caja no encontrada o ya cerrada'; end if;
  select cr.opening_amount + coalesce(sum(case when cm.movement_type='ingreso' then cm.amount else -cm.amount end),0)
    into v_expected from public.cash_registers cr left join public.cash_movements cm on cm.cash_register_id=cr.id
    where cr.id=p_register_id group by cr.id;
  if v_opened_by <> auth.uid() and not public.has_permission('cash.close_any') then raise exception 'Solo quien abrió la caja puede cerrarla'; end if;
  update public.cash_registers set status='cerrada', closed_by=auth.uid(), closed_at=now(), expected_amount=v_expected,
    counted_amount=p_counted_amount, difference=p_counted_amount-v_expected where id=p_register_id;
  return jsonb_build_object('expected',v_expected,'counted',p_counted_amount,'difference',p_counted_amount-v_expected);
end $$;

create or replace function public.register_sale(
  p_customer_id uuid, p_cash_register_id uuid, p_items jsonb, p_discount numeric,
  p_payment_amount numeric, p_payment_method text, p_order_id uuid default null,
  p_idempotency_key uuid default gen_random_uuid()
) returns uuid language plpgsql security definer set search_path = public as $$
declare item jsonb; v_variant uuid; v_qty numeric; v_price numeric; v_stock numeric;
        v_subtotal numeric := 0; v_total numeric; v_sale uuid; v_payment uuid;
begin
  if not public.has_permission('sales.write') then raise exception 'No autorizado'; end if;
  select id into v_sale from public.sales where idempotency_key=p_idempotency_key;
  if found then return v_sale; end if;
  if p_payment_method not in ('efectivo','yape','plin','transferencia','tarjeta') then raise exception 'Forma de pago inválida'; end if;
  if jsonb_typeof(p_items) <> 'array' or jsonb_array_length(p_items)=0 then raise exception 'La venta no contiene productos'; end if;
  perform 1 from public.cash_registers where id=p_cash_register_id and status='abierta' for update;
  if not found then raise exception 'La caja no está abierta'; end if;
  for item in select * from jsonb_array_elements(p_items) loop
    v_variant := (item->>'variant_id')::uuid; v_qty := (item->>'quantity')::numeric; v_price := (item->>'unit_price')::numeric;
    if v_qty <= 0 or v_price < 0 then raise exception 'Cantidad o precio inválido'; end if;
    select stock into v_stock from public.product_variants where id=v_variant and is_active for update;
    if not found or v_stock < v_qty then raise exception 'Stock insuficiente para la variante %', v_variant; end if;
    v_subtotal := v_subtotal + v_qty*v_price;
  end loop;
  v_total := greatest(0, v_subtotal-coalesce(p_discount,0));
  if p_payment_amount < 0 or p_payment_amount > v_total then raise exception 'Monto de pago inválido'; end if;
  insert into public.sales(customer_id,order_id,cash_register_id,subtotal,discount,total,paid,balance,idempotency_key,created_by)
    values(p_customer_id,p_order_id,p_cash_register_id,v_subtotal,coalesce(p_discount,0),v_total,p_payment_amount,v_total-p_payment_amount,p_idempotency_key,auth.uid()) returning id into v_sale;
  for item in select * from jsonb_array_elements(p_items) loop
    v_variant := (item->>'variant_id')::uuid; v_qty := (item->>'quantity')::numeric; v_price := (item->>'unit_price')::numeric;
    insert into public.sale_details(sale_id,variant_id,quantity,unit_price) values(v_sale,v_variant,v_qty,v_price);
    update public.product_variants set stock=stock-v_qty, updated_at=now() where id=v_variant returning stock into v_stock;
    insert into public.stock_movements(variant_id,movement_type,quantity,balance_after,reason,reference,idempotency_key,created_by)
      values(v_variant,'salida',v_qty,v_stock,'Venta',v_sale::text,gen_random_uuid(),auth.uid());
  end loop;
  if p_payment_amount > 0 then
    insert into public.payments(sale_id,amount,method,created_by) values(v_sale,p_payment_amount,p_payment_method,auth.uid()) returning id into v_payment;
    insert into public.cash_movements(cash_register_id,movement_type,amount,reason,payment_id,created_by)
      values(p_cash_register_id,'ingreso',p_payment_amount,'Pago de venta '||v_sale,v_payment,auth.uid());
  end if;
  insert into public.audit_logs(user_id,table_name,record_id,action,new_data)
    values(auth.uid(),'sales',v_sale::text,'RPC',jsonb_build_object('idempotency_key',p_idempotency_key));
  return v_sale;
end $$;

create or replace function public.convert_quotation_to_order(p_quotation_id uuid) returns uuid
language plpgsql security definer set search_path = public as $$
declare q public.quotations; v_order uuid;
begin
  if not public.has_permission('orders.write') then raise exception 'No autorizado'; end if;
  select * into q from public.quotations where id=p_quotation_id for update;
  if not found or q.status <> 'aprobada' then raise exception 'La cotización debe estar aprobada'; end if;
  if exists(select 1 from public.orders where quotation_id=p_quotation_id) then raise exception 'La cotización ya fue convertida'; end if;
  insert into public.orders(quotation_id,customer_id,delivery_date,total,balance,created_by)
    values(q.id,q.customer_id,q.estimated_delivery,q.total,q.total,auth.uid()) returning id into v_order;
  insert into public.order_details(order_id,description,quantity,sizes,colors,unit_price)
    select v_order, garment_type||' / '||service, quantity, sizes, colors, unit_price from public.quotation_details where quotation_id=q.id;
  return v_order;
end $$;

create or replace function public.update_order_status(p_order_id uuid, p_status text, p_notes text default null) returns void
language plpgsql security definer set search_path = public as $$
declare v_old text;
begin
  if not public.has_permission('orders.write') and not public.has_permission('production.write') then raise exception 'No autorizado'; end if;
  select status into v_old from public.orders where id=p_order_id for update;
  if not found then raise exception 'Pedido no encontrado'; end if;
  update public.orders set status=p_status, updated_at=now() where id=p_order_id;
  insert into public.order_status_history(order_id,from_status,to_status,notes,changed_by) values(p_order_id,v_old,p_status,p_notes,auth.uid());
end $$;

-- Indicadores y reportes respetan las políticas RLS del usuario que invoca.
create or replace function public.dashboard_metrics() returns jsonb language sql stable as $$
select jsonb_build_object(
  'products',(select count(*) from public.products where is_active),
  'total_stock',(select coalesce(sum(stock),0) from public.product_variants where is_active),
  'low_stock',(select count(*) from public.product_variants v join public.products p on p.id=v.product_id where v.stock<=p.minimum_stock and v.is_active),
  'active_customers',(select count(*) from public.customers where is_active),
  'pending_quotes',(select count(*) from public.quotations where status in ('borrador','enviada')),
  'production_orders',(select count(*) from public.orders where status not in ('registrado','entregado','cancelado')),
  'delivered_orders',(select count(*) from public.orders where status='entregado'),
  'daily_sales',(select coalesce(sum(total),0) from public.sales where sale_date::date=current_date and status='confirmada'),
  'monthly_sales',(select coalesce(sum(total),0) from public.sales where date_trunc('month',sale_date)=date_trunc('month',now()) and status='confirmada'),
  'total_income',(select coalesce(sum(amount),0) from public.payments)
) $$;

create or replace function public.sales_last_30_days() returns table(day date,total numeric) language sql stable as $$
select d::date, coalesce(sum(s.total),0) from generate_series(current_date-29,current_date,'1 day') d
left join public.sales s on s.sale_date::date=d::date and s.status='confirmada' group by d order by d $$;

create or replace function public.global_search(p_query text) returns table(entity text,record_id uuid,title text,subtitle text) language sql stable as $$
  select * from (
    select 'Producto'::text,p.id,p.name,(p.sku||' · '||p.product_type)::text from public.products p where p.name ilike '%'||p_query||'%' or p.sku ilike '%'||p_query||'%'
    union all select 'Cliente',c.id,c.name,coalesce(c.document_number,'') from public.customers c where c.name ilike '%'||p_query||'%' or c.document_number ilike '%'||p_query||'%'
    union all select 'Pedido',o.id,o.number,(o.status||' · '||c.name) from public.orders o join public.customers c on c.id=o.customer_id where o.number ilike '%'||p_query||'%' or c.name ilike '%'||p_query||'%'
    union all select 'Cotización',q.id,q.number,(q.status||' · '||c.name) from public.quotations q join public.customers c on c.id=q.customer_id where q.number ilike '%'||p_query||'%' or c.name ilike '%'||p_query||'%'
  ) x limit 50
$$;

create or replace function public.estimate_embroidery_minutes(p_stitches integer,p_quantity integer,p_stitches_per_minute integer default 800,p_efficiency numeric default 0.80,p_heads integer default 12)
returns integer language plpgsql immutable as $$
begin
  if p_stitches<0 or p_quantity<1 or p_stitches_per_minute<1 or p_efficiency<=0 or p_efficiency>1 or p_heads<1 then raise exception 'Parámetros inválidos'; end if;
  return ceil((p_stitches::numeric * ceil(p_quantity::numeric/p_heads)) / (p_stitches_per_minute*p_efficiency));
end $$;

create or replace function public.inventory_report() returns table(sku text,name text,size text,color text,stock numeric,value numeric) language sql stable as $$
select p.sku,p.name,v.size,v.color,v.stock,v.stock*p.cost from public.products p join public.product_variants v on v.product_id=p.id where p.is_active and v.is_active order by p.name $$;
create or replace function public.kardex_report() returns table(created_at timestamptz,sku text,movement_type text,quantity numeric,balance numeric,reason text) language sql stable as $$
select m.created_at,p.sku,m.movement_type,m.quantity,m.balance_after,m.reason from public.stock_movements m join public.product_variants v on v.id=m.variant_id join public.products p on p.id=v.product_id order by m.created_at desc limit 5000 $$;
create or replace function public.sales_report() returns table(sale_date timestamptz,number text,customer text,total numeric,paid numeric,balance numeric) language sql stable as $$
select s.sale_date,s.number,coalesce(c.name,'Público general'),s.total,s.paid,s.balance from public.sales s left join public.customers c on c.id=s.customer_id order by s.sale_date desc $$;
create or replace function public.pending_orders_report() returns table(number text,customer text,status text,delivery_date date,balance numeric) language sql stable as $$
select o.number,c.name,o.status,o.delivery_date,o.balance from public.orders o join public.customers c on c.id=o.customer_id where o.status not in ('entregado','cancelado') order by o.delivery_date nulls last $$;
create or replace function public.production_report() returns table(number text,operator text,status text,quantity integer,approved integer,defective integer) language sql stable as $$
select e.number,coalesce(p.full_name,'Sin asignar'),e.status,e.quantity,e.approved_pieces,e.defective_pieces from public.embroidery_jobs e left join public.profiles p on p.id=e.operator_id order by e.created_at desc $$;
create or replace function public.purchases_report() returns table(purchase_date date,number text,supplier text,total numeric,paid numeric) language sql stable as $$
select p.purchase_date,p.number,s.name,p.total,p.paid from public.purchases p join public.suppliers s on s.id=p.supplier_id order by p.purchase_date desc $$;

revoke all on function public.register_stock_movement(uuid,text,numeric,text,text,uuid,uuid) from public;
revoke all on function public.register_sale(uuid,uuid,jsonb,numeric,numeric,text,uuid,uuid) from public;
revoke all on function public.open_cash_register(numeric), public.close_cash_register(uuid,numeric), public.convert_quotation_to_order(uuid), public.update_order_status(uuid,text,text) from public;
grant execute on all functions in schema public to authenticated;

