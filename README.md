# Cordón de Oro — Sistema de Gestión Empresarial

Aplicación de escritorio para Windows 10/11 construida con Python 3.12, PySide6 y Supabase. La información empresarial reside en PostgreSQL/Supabase; el equipo local conserva únicamente una caché de lectura cifrada con Windows DPAPI para contingencias de conexión.

## Funcionalidad incluida

- Supabase Auth por correo/contraseña, recuperación de contraseña, cierre y renovación gestionada por el SDK.
- Siete roles y permisos aplicados mediante RLS, no solo mediante controles visuales.
- Dashboard con indicadores y ventas de 30 días.
- Inventario, variantes por talla/color, kardex, importación Excel, código de barras y movimientos transaccionales.
- CRM de clientes y acceso a WhatsApp.
- Cotizaciones y conversión atómica a pedidos.
- Pedidos con once etapas e historial de estados.
- Producción y órdenes de bordado para 12 cabezales, con función de estimación parametrizable.
- POS, pagos parciales, apertura/cierre de caja y descuento de stock en una sola transacción.
- Proveedores, compras y reportes PDF/Excel.
- Storage privado, URLs firmadas disponibles por SDK, validación de tamaño/MIME y políticas por rol.
- Realtime para inventario, pedidos, cotizaciones, producción, CRM y notificaciones.
- Auditoría de entidades críticas e idempotencia para ventas y movimientos de stock.
- Tema claro/oscuro, interfaz adaptable e instalador Inno Setup.

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

Requiere Python 3.12+ de 64 bits.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` con la URL y la clave `anon`/publicable del proyecto. Nunca use `service_role`.

```powershell
python main.py
```

## Construcción e instalador

Instale Inno Setup 6 y agregue el logo/icono original según `assets/README.md`. Luego:

```powershell
.\build.ps1
```

El resultado se crea en `output\CordonDeOro-Setup-0.1.0.exe`. El instalador incluye el runtime de Python producido por PyInstaller; los equipos finales no necesitan instalar Python.

## Actualizaciones mediante GitHub

La aplicación consulta al iniciar la última versión publicada en GitHub Releases. También incluye el botón **Actualizaciones**. La descarga solo se ejecuta con confirmación del usuario y se instala después de verificar su SHA-256.

1. Configure `GITHUB_REPOSITORY=propietario/repositorio` en `.env`. El repositorio de esta instalación es `nexvorytech12/cordon-oro-desktop`.
2. En GitHub, cree las variables del repositorio `SUPABASE_URL` y `SUPABASE_ANON_KEY` en **Settings → Secrets and variables → Actions → Variables**. Ambas son credenciales públicas del cliente; nunca agregue `service_role`.
3. Suba los cambios y publique una etiqueta semántica:

   ```powershell
   git tag v0.2.0
   git push origin main --tags
   ```

El flujo `.github/workflows/release.yml` ejecuta pruebas, genera el instalador, calcula su checksum y crea la versión de GitHub. Los equipos instalados detectarán `v0.2.0` automáticamente.

Después de instalar, copie `.env.example` como `.env` junto al ejecutable y complete los dos valores públicos. Alternativamente cree `%LOCALAPPDATA%\Cordón de Oro\.env`.

## Operación sin conexión

Supabase continúa siendo la única fuente oficial. Las consultas exitosas se guardan cifradas para el usuario de Windows y pueden mostrarse cuando la red cae. Las altas, ediciones, ventas, movimientos de stock, pagos y cierres de caja se rechazan sin confirmación del servidor; no existe una cola de escrituras que pueda producir conflictos. Realtime vuelve a actualizar las vistas tras la reconexión.

## Pruebas

```powershell
python -m pytest
```

Las migraciones deben validarse también en un proyecto Supabase de staging antes de producción. Para una salida productiva, ensaye al menos: venta simultánea del último stock desde dos equipos, reintento con la misma clave idempotente, cierre de caja ajena, aislamiento de cada rol, acceso a buckets privados, reconexión Realtime y restauración desde copia de seguridad.

## Límites conscientes

- No se simula conexión directa con la bordadora; el módulo registra y calcula trabajos.
- La facturación SUNAT queda como punto de integración futura. No se emiten comprobantes fiscales sin un proveedor/OSE y credenciales válidas.
- El logo original no fue entregado dentro del proyecto; se dejó el punto de incorporación sin inventar una marca sustituta.

