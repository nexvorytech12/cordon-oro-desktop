# Manual breve de instalación

1. El administrador instala `CordonDeOro-Setup-0.1.0.exe` en cada PC Windows 10/11.
2. Copia el archivo de configuración `.env` preparado por TI al directorio de la aplicación o a `%LOCALAPPDATA%\Cordón de Oro\.env`.
3. Verifica fecha/hora de Windows y conectividad HTTPS hacia el dominio del proyecto Supabase.
4. Inicia la aplicación desde el acceso directo e ingresa con el correo empresarial.
5. Si la cuenta aparece desactivada, un administrador debe activarla y asignarle un rol desde Usuarios.

Para actualizar, instale la versión nueva sobre la anterior. Los datos no viven en el equipo y no se eliminan al desinstalar. La caché cifrada local se encuentra en `%LOCALAPPDATA%\Cordón de Oro\cache` y puede borrarse después de cerrar la aplicación.

Ante un error, consulte `%LOCALAPPDATA%\Cordón de Oro\cordon_de_oro.log`. Nunca envíe el archivo `.env` ni tokens de sesión por correo o mensajería.

