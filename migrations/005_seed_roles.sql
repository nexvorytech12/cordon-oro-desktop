insert into public.roles(name,description) values
('administrador','Control total del sistema'),('gerencia','Indicadores, aprobaciones y reportes'),
('atención_cliente','CRM, cotizaciones y seguimiento'),('ventas','Ventas, clientes y pedidos'),
('almacén','Productos, stock, compras y proveedores'),('producción','Pedidos y procesos productivos'),
('caja','Punto de venta, pagos y caja') on conflict(name) do nothing;

insert into public.permissions(code,description) values
('users.manage','Gestionar usuarios, roles y permisos'),('audit.read','Consultar auditoría'),('storage.manage','Administrar archivos'),
('customers.read','Consultar clientes'),('customers.write','Gestionar clientes'),
('inventory.read','Consultar inventario'),('inventory.write','Gestionar inventario'),
('quotations.read','Consultar cotizaciones'),('quotations.write','Gestionar cotizaciones'),
('orders.read','Consultar pedidos'),('orders.write','Gestionar pedidos'),
('production.read','Consultar producción'),('production.write','Gestionar producción'),
('sales.read','Consultar ventas'),('sales.write','Registrar ventas'),
('cash.read','Consultar caja'),('cash.write','Operar caja'),('cash.close_any','Cerrar cajas de otros usuarios'),
('purchases.read','Consultar compras'),('purchases.write','Gestionar compras'),('reports.read','Generar reportes')
on conflict(code) do nothing;

-- El administrador recibe todos los permisos.
insert into public.role_permissions(role_id,permission_id)
select r.id,p.id from public.roles r cross join public.permissions p where r.name='administrador'
on conflict do nothing;

-- Asignaciones de menor privilegio por responsabilidad.
with grants(role_name, permission_code) as (values
('gerencia','customers.read'),('gerencia','inventory.read'),('gerencia','quotations.read'),('gerencia','quotations.write'),
('gerencia','orders.read'),('gerencia','orders.write'),('gerencia','production.read'),('gerencia','sales.read'),
('gerencia','cash.read'),('gerencia','purchases.read'),('gerencia','reports.read'),('gerencia','audit.read'),
('atención_cliente','customers.read'),('atención_cliente','customers.write'),('atención_cliente','quotations.read'),
('atención_cliente','quotations.write'),('atención_cliente','orders.read'),
('ventas','customers.read'),('ventas','customers.write'),('ventas','inventory.read'),('ventas','quotations.read'),
('ventas','quotations.write'),('ventas','orders.read'),('ventas','orders.write'),('ventas','sales.read'),('ventas','sales.write'),
('almacén','inventory.read'),('almacén','inventory.write'),('almacén','orders.read'),('almacén','purchases.read'),
('almacén','purchases.write'),('almacén','reports.read'),
('producción','inventory.read'),('producción','orders.read'),('producción','orders.write'),('producción','production.read'),
('producción','production.write'),('producción','reports.read'),
('caja','customers.read'),('caja','inventory.read'),('caja','orders.read'),('caja','sales.read'),('caja','sales.write'),
('caja','cash.read'),('caja','cash.write'),('caja','reports.read')
)
insert into public.role_permissions(role_id,permission_id)
select r.id,p.id from grants g join public.roles r on r.name=g.role_name join public.permissions p on p.code=g.permission_code
on conflict do nothing;

insert into public.categories(name,description) values
('Polos','Prendas tipo polo'),('Camisas','Camisas y blusas'),('Pantalones','Pantalones y shorts'),
('Uniformes','Uniformes escolares y empresariales'),('Abrigo','Casacas, poleras y chaquetas'),
('Telas','Telas e insumos textiles'),('Hilos','Hilos de confección y bordado'),('Avíos','Botones, cierres, elásticos y etiquetas')
on conflict(name) do nothing;
insert into public.warehouses(name,address) values('Almacén principal','Sede principal') on conflict(name) do nothing;

-- BOOTSTRAP DEL PRIMER ADMINISTRADOR (ejecutar una sola vez tras crear el usuario en Auth):
-- update public.profiles set role_id=(select id from public.roles where name='administrador'), is_active=true
-- where id='UUID_DEL_USUARIO';

