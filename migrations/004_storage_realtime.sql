-- Buckets privados y validación de tipo/tamaño en Storage.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types) values
('product-images','product-images',false,5242880,array['image/jpeg','image/png','image/webp']),
('embroidery-designs','embroidery-designs',false,20971520,array['image/jpeg','image/png','application/pdf','application/octet-stream']),
('quotations','quotations',false,10485760,array['application/pdf','image/jpeg','image/png']),
('internal-receipts','internal-receipts',false,10485760,array['application/pdf','image/jpeg','image/png']),
('customer-documents','customer-documents',false,10485760,array['application/pdf','image/jpeg','image/png'])
on conflict(id) do update set public=false,file_size_limit=excluded.file_size_limit,allowed_mime_types=excluded.allowed_mime_types;

create policy storage_authorized_read on storage.objects for select to authenticated
using (
  (bucket_id='product-images' and public.has_permission('inventory.read')) or
  (bucket_id='embroidery-designs' and public.has_permission('production.read')) or
  (bucket_id='quotations' and public.has_permission('quotations.read')) or
  (bucket_id='internal-receipts' and (public.has_permission('sales.read') or public.has_permission('purchases.read'))) or
  (bucket_id='customer-documents' and public.has_permission('customers.read'))
);
create policy storage_authorized_insert on storage.objects for insert to authenticated
with check (
  owner_id=auth.uid()::text and (
    (bucket_id='product-images' and public.has_permission('inventory.write')) or
    (bucket_id='embroidery-designs' and public.has_permission('production.write')) or
    (bucket_id='quotations' and public.has_permission('quotations.write')) or
    (bucket_id='internal-receipts' and (public.has_permission('sales.write') or public.has_permission('purchases.write'))) or
    (bucket_id='customer-documents' and public.has_permission('customers.write'))
  )
);
create policy storage_owner_update on storage.objects for update to authenticated
using (owner_id=auth.uid()::text) with check (owner_id=auth.uid()::text);
create policy storage_owner_delete on storage.objects for delete to authenticated
using (owner_id=auth.uid()::text or public.has_permission('storage.manage'));

-- Tablas publicadas para sincronización entre equipos.
alter publication supabase_realtime add table public.product_variants;
alter publication supabase_realtime add table public.stock_movements;
alter publication supabase_realtime add table public.orders;
alter publication supabase_realtime add table public.order_status_history;
alter publication supabase_realtime add table public.quotations;
alter publication supabase_realtime add table public.production_orders;
alter publication supabase_realtime add table public.embroidery_jobs;
alter publication supabase_realtime add table public.customer_interactions;
alter publication supabase_realtime add table public.notifications;

