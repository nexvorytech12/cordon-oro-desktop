# Manual breve de instalación

1. El administrador ejecuta `CordonDeOro-Setup-0.2.0.exe` en cada PC con Windows 10/11.
2. Selecciona la carpeta de instalación y deja activada la creación del acceso directo.
3. Inicia **Cordón de Oro** e ingresa con el correo empresarial.
4. Verifica en **Configuración** que la conexión con Supabase figure como conectada.
5. Si una cuenta está desactivada, un administrador debe activarla y asignarle un rol desde **Usuarios**.

La URL y la clave publicable de Supabase se incorporan durante la compilación; el instalador no requiere copiar un archivo `.env` al equipo del usuario. Nunca incluya una clave `service_role` en el proyecto de escritorio.

Las nuevas versiones se publican en GitHub. La aplicación puede buscarlas al iniciar, descargarlas y ejecutar el instalador actualizado. Los datos empresariales permanecen en Supabase y no se eliminan al desinstalar la aplicación.

Para generar un instalador local, instale Node.js 24 o posterior y ejecute `./build.ps1`. El resultado se guarda en `release\`.

