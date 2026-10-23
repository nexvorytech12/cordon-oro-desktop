# Cordón de Oro — Sistema de Gestión Empresarial

Aplicación de escritorio para Windows desarrollada con **Electron, React y TypeScript**, conectada directamente con Supabase.

## Tecnología actual

- Electron 45 y React 19.
- TypeScript y Vite.
- Supabase Auth, PostgreSQL, Storage y Realtime.
- Recharts para indicadores y gráficos.
- ExcelJS y jsPDF para reportes.
- electron-builder/NSIS para el instalador de Windows.
- electron-updater para actualizaciones desde GitHub Releases.

La implementación anterior en Python/PySide6 se conserva temporalmente como referencia durante la transición, pero el instalador desde la versión `0.2.0` utiliza Electron.

## Funcionalidad incluida

- Supabase Auth por correo/contraseña, recuperación de contraseña, cierre y renovación gestionada por el SDK.
- Siete roles y permisos aplicados mediante RLS, no solo mediante controles visuales.
- Dashboard con indicadores y ventas de 30 días.
- Inventario, variantes por talla/color, kardex y movimientos transaccionales.
- CRM de clientes y acceso a WhatsApp.
- Cotizaciones y conversión atómica a pedidos.
- Pedidos con once etapas e historial de estados.
- Producción y órdenes de bordado para 12 cabezales, con función de estimación parametrizable.
- POS, pagos parciales, apertura/cierre de caja y descuento de stock en una sola transacción.
- Proveedores, compras y reportes PDF/Excel.
- Storage privado, URLs firmadas disponibles por SDK, validación de tamaño/MIME y políticas por rol.
- Realtime para inventario, pedidos, cotizaciones, producción, CRM y notificaciones.
- Auditoría de entidades críticas e idempotencia para ventas y movimientos de stock.
- Tema claro/oscuro, interfaz adaptable e instalador NSIS.

## Puesta en marcha de Supabase

1. Cree un proyecto de Supabase y vincúlelo con Supabase CLI.
2. Ejecute en orden los archivos de `migrations/` mediante `supabase db push` o desde el editor SQL.
3. Cree el primer usuario en Authentication > Users.
4. Ejecute la instrucción de bootstrap comentada al final de `005_seed_roles.sql`, sustituyendo el UUID. Esta es la única activación manual necesaria.
5. Despliegue la función segura de usuarios:

   ```powershell
   supabase functions deploy create-user
   ```

   `SUPABASE_SERVICE_ROLE_KEY` existe únicamente como secreto administrado por el entorno de Edge Functions; jamás se copia al escritorio.

6. En Authentication > URL Configuration, configure la URL de recuperación apropiada para su organización.

## Ejecución local

Requiere Node.js 24.

```powershell
npm ci
Copy-Item .env.example .env
```

Edite `.env` con la URL y la clave `anon`/publicable del proyecto. Nunca use `service_role`.

```powershell
npm run dev
```

## Construcción e instalador

Para crear la aplicación y el instalador NSIS:

```powershell
npm run dist
```

El resultado se crea en `release\CordonDeOro-Setup-<versión>.exe`. El instalador incluye Electron y todas las dependencias; los equipos finales no necesitan instalar Node.js.

## Actualizaciones mediante GitHub

La aplicación consulta GitHub Releases mediante `electron-updater`. La descarga e instalación se controlan desde **Configuración → Actualizaciones** y se validan mediante los metadatos de integridad generados por electron-builder.

1. En GitHub, configure las variables `SUPABASE_URL` y `SUPABASE_ANON_KEY` en **Settings → Secrets and variables → Actions → Variables**. Ambas son credenciales públicas del cliente; nunca agregue `service_role`.
2. Suba los cambios y publique una etiqueta semántica:

   ```powershell
   git tag v0.2.1
   git push origin main --tags
   ```

El flujo `.github/workflows/release.yml` audita dependencias, ejecuta pruebas, genera el instalador, calcula su checksum y publica los archivos necesarios para las actualizaciones. Los valores públicos de Supabase se incorporan durante la compilación.

## Operación sin conexión

Supabase continúa siendo la única fuente oficial. La sesión se conserva de forma local mediante el SDK oficial, pero las operaciones empresariales requieren confirmación del servidor. No existe una cola de escrituras offline que pueda producir conflictos. Realtime vuelve a actualizar las vistas tras la reconexión.

## Pruebas

```powershell
npm test
npm audit --audit-level=moderate
```

Las migraciones deben validarse también en un proyecto Supabase de staging antes de producción. Para una salida productiva, ensaye al menos: venta simultánea del último stock desde dos equipos, reintento con la misma clave idempotente, cierre de caja ajena, aislamiento de cada rol, acceso a buckets privados, reconexión Realtime y restauración desde copia de seguridad.

## Límites conscientes

- No se simula conexión directa con la bordadora; el módulo registra y calcula trabajos.
- La facturación SUNAT queda como punto de integración futura. No se emiten comprobantes fiscales sin un proveedor/OSE y credenciales válidas.
- La implementación Python anterior permanece temporalmente en el repositorio como referencia y puede retirarse cuando la versión Electron complete la validación operativa en producción.

