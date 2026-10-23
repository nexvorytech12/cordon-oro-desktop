from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class LoginWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, service: SupabaseService, email: str, password: str):
        super().__init__()
        self.service, self.email, self.password = service, email, password

    def run(self) -> None:
        try:
            self.succeeded.emit(self.service.sign_in(self.email, self.password))
        except Exception as exc:
            logger.warning("Inicio de sesión rechazado: %s", exc)
            self.failed.emit(str(exc))


class LoginWindow(QMainWindow):
    def __init__(self, service: SupabaseService):
        super().__init__()
        self.service = service
        self.worker: LoginWorker | None = None
        self.main_window = None
        self.setWindowTitle("Cordón de Oro — Acceso")
        self.setMinimumSize(900, 570)
        self._build()

    def _build(self) -> None:
        root = QWidget(objectName="page")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)

        hero = QFrame(objectName="sidebar")
        hero.setMinimumWidth(390)
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(55, 55, 55, 55)
        hero_layout.addStretch()
        mark = QLabel("CO")
        mark.setStyleSheet("font-size: 42pt; font-weight: 800; color: #C5A052;")
        hero_layout.addWidget(mark)
        title = QLabel("CORDÓN DE ORO")
        title.setStyleSheet("font-size: 22pt; font-weight: 700; color: white;")
        hero_layout.addWidget(title)
        subtitle = QLabel("Gestión empresarial para confección,\nbordado y comercialización")
        subtitle.setStyleSheet("font-size: 12pt; color: #CBD5DF; line-height: 1.4;")
        hero_layout.addWidget(subtitle)
        hero_layout.addStretch(2)
        safe = QLabel("🔒 Sesión protegida por Supabase Auth")
        safe.setStyleSheet("color: #96AABE;")
        hero_layout.addWidget(safe)

        panel = QWidget(objectName="page")
        form = QVBoxLayout(panel)
        form.setContentsMargins(80, 60, 80, 60)
        form.addStretch()
        heading = QLabel("Bienvenido")
        heading.setObjectName("heading")
        form.addWidget(heading)
        hint = QLabel("Ingrese con su cuenta empresarial")
        hint.setObjectName("muted")
        form.addWidget(hint)
        form.addSpacing(24)
        form.addWidget(QLabel("Correo electrónico"))
        self.email = QLineEdit()
        self.email.setPlaceholderText("usuario@cordondeoro.pe")
        self.email.setClearButtonEnabled(True)
        form.addWidget(self.email)
        form.addWidget(QLabel("Contraseña"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("••••••••")
        self.password.returnPressed.connect(self._login)
        form.addWidget(self.password)
        self.show_password = QCheckBox("Mostrar contraseña")
        self.show_password.toggled.connect(
            lambda checked: self.password.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        )
        form.addWidget(self.show_password)
        form.addSpacing(12)
        self.login_button = QPushButton("INICIAR SESIÓN", objectName="gold")
        self.login_button.clicked.connect(self._login)
        form.addWidget(self.login_button)
        reset = QPushButton("Olvidé mi contraseña")
        reset.setFlat(True)
        reset.clicked.connect(self._reset_password)
        form.addWidget(reset, alignment=Qt.AlignmentFlag.AlignCenter)
        form.addStretch()
        layout.addWidget(hero, 4)
        layout.addWidget(panel, 6)
        self.setCentralWidget(root)

    def _login(self) -> None:
        email, password = self.email.text().strip(), self.password.text()
        if not email or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingrese correo y contraseña.")
            return
        self.login_button.setEnabled(False)
        self.login_button.setText("CONECTANDO…")
        self.worker = LoginWorker(self.service, email, password)
        self.worker.succeeded.connect(self._open_app)
        self.worker.failed.connect(self._login_failed)
        self.worker.start()

    def _open_app(self, session: object) -> None:
        from ui.main_window import MainWindow
        self.main_window = MainWindow(self.service, session)
        self.main_window.showMaximized()
        self.close()

    def _login_failed(self, message: str) -> None:
        self.login_button.setEnabled(True)
        self.login_button.setText("INICIAR SESIÓN")
        QMessageBox.critical(self, "Acceso denegado", message or "Credenciales incorrectas.")

    def _reset_password(self) -> None:
        email = self.email.text().strip()
        if not email:
            QMessageBox.information(self, "Recuperar contraseña", "Escriba primero su correo electrónico.")
            return
        try:
            self.service.reset_password(email)
            QMessageBox.information(self, "Correo enviado", "Revise su bandeja para continuar la recuperación.")
        except Exception as exc:
            QMessageBox.critical(self, "No fue posible enviar", str(exc))

