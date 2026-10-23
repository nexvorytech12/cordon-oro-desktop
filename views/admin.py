from PySide6.QtWidgets import QDialog, QMessageBox

from services.supabase_service import SupabaseService
from views.crud import CrudView, Field, RecordDialog


class UsersView(CrudView):
    """Activa usuarios creados en Supabase Auth y les asigna rol; nunca administra contraseñas."""
    def __init__(self, service: SupabaseService):
        super().__init__(service, title="Usuarios y permisos", table="profiles", permission="users.manage",
            select="id,full_name,phone,is_active,role_id,roles(name),created_at",
            columns=[("full_name","Nombre"),("phone","Teléfono"),("roles.name","Rol"),("is_active","Activo"),("created_at","Creado")],
            fields=[Field("full_name","Nombre completo",required=True),Field("phone","Teléfono"),Field("role_id","ID del rol",required=True),Field("is_active","Cuenta activa","bool")])

    def create(self) -> None:
        dialog = RecordDialog("Crear usuario", [Field("email","Correo",required=True),Field("password","Contraseña temporal","password",True),Field("full_name","Nombre completo",required=True),Field("role_id","ID del rol",required=True)], parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                response = self.service.client.functions.invoke("create-user", {"body": dialog.data()})
                if getattr(response, "status_code", 200) >= 300: raise RuntimeError(str(getattr(response,"data",response)))
                QMessageBox.information(self,"Usuario creado","La cuenta quedó activa. Solicite al usuario cambiar su contraseña."); self.refresh()
            except Exception as exc: QMessageBox.critical(self,"No se pudo crear",str(exc))

