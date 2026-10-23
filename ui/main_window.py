from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QObject, QProcess, QPropertyAnimation, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QLineEdit, QProgressDialog, QPushButton, QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)

from models.session import UserSession
from services.supabase_service import SupabaseService
from services.update_service import ReleaseInfo, UpdateService
from ui.styles import stylesheet
from views.dashboard import DashboardView
from views.modules import CustomersView, InventoryView, orders_view, production_view, purchases_view, quotations_view, suppliers_view
from views.reports_view import ReportsView
from views.sales import CashView, SalesView
from views.admin import UsersView


class RealtimeBridge(QObject):
    changed = Signal(str)


class UpdateWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, updater: UpdateService, release: ReleaseInfo | None = None):
        super().__init__()
        self.updater, self.release = updater, release

    def run(self) -> None:
        try:
            self.completed.emit(self.updater.download(self.release) if self.release else self.updater.check())
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, service: SupabaseService, session: UserSession):
        super().__init__(); self.service, self.session = service, session; self.dark = False
        self.setWindowTitle("Cordón de Oro — Sistema de Gestión Empresarial")
        self.setMinimumSize(1180, 720); self.bridge = RealtimeBridge(self); self.bridge.changed.connect(self._realtime_changed)
        self.updater = UpdateService(service.settings); self.update_worker = None; self.update_progress = None
        self._build()
        self._subscribe()
        self.connection_timer = QTimer(self); self.connection_timer.timeout.connect(self._connection_status); self.connection_timer.start(3000)
        QTimer.singleShot(4000, lambda: self._check_updates(silent=True))

    def _build(self) -> None:
        central = QWidget(objectName="page"); root = QHBoxLayout(central); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        self.sidebar = QFrame(objectName="sidebar"); self.sidebar.setMinimumWidth(225); self.sidebar.setMaximumWidth(225)
        nav = QVBoxLayout(self.sidebar); nav.setContentsMargins(12, 18, 12, 18)
        brand = QLabel("CORDÓN DE ORO"); brand.setObjectName("brand"); nav.addWidget(brand)
        subtitle = QLabel("GESTIÓN EMPRESARIAL"); subtitle.setStyleSheet("color:#91A0B0; font-size:8pt; letter-spacing:1px;"); nav.addWidget(subtitle); nav.addSpacing(18)
        self.stack = QStackedWidget()
        pages = [
            ("▦  Dashboard", DashboardView(self.service)),
            ("▣  Inventario", InventoryView(self.service)),
            ("♙  Clientes / CRM", CustomersView(self.service)),
            ("≡  Cotizaciones", quotations_view(self.service)),
            ("◫  Pedidos", orders_view(self.service)),
            ("⚙  Producción", production_view(self.service)),
            ("$  Punto de venta", SalesView(self.service)),
            ("▤  Caja", CashView(self.service)),
            ("◆  Proveedores", suppliers_view(self.service)),
            ("↓  Compras", purchases_view(self.service)),
            ("▥  Reportes", ReportsView(self.service)),
        ]
        if self.session.can("users.manage"):
            pages.append(("♟  Usuarios", UsersView(self.service)))
        self.nav_buttons = []
        for i, (label, page) in enumerate(pages):
            button = QPushButton(label, objectName="nav"); button.setCheckable(True); button.clicked.connect(lambda _=False, index=i: self._show(index))
            nav.addWidget(button); self.nav_buttons.append(button); self.stack.addWidget(page)
        nav.addStretch()
        collapse = QPushButton("☰  Contraer", objectName="nav"); collapse.clicked.connect(self._toggle_sidebar); nav.addWidget(collapse)
        root.addWidget(self.sidebar)
        right = QWidget(objectName="page"); right_layout = QVBoxLayout(right); right_layout.setContentsMargins(0, 0, 0, 0); right_layout.setSpacing(0)
        top = QFrame(objectName="card"); top.setFixedHeight(58); top_layout = QHBoxLayout(top); top_layout.setContentsMargins(18, 8, 18, 8)
        top_layout.addWidget(QLabel(f"{self.session.full_name}  ·  {self.session.role.replace('_', ' ').title()}")); top_layout.addStretch()
        self.global_search = QLineEdit(); self.global_search.setPlaceholderText("Buscar producto, cliente o pedido…"); self.global_search.setMaximumWidth(320); self.global_search.returnPressed.connect(self._search); top_layout.addWidget(self.global_search)
        theme = QPushButton("◐ Tema"); theme.clicked.connect(self._theme); top_layout.addWidget(theme)
        updates = QPushButton("↻ Actualizaciones"); updates.clicked.connect(lambda: self._check_updates(silent=False)); top_layout.addWidget(updates)
        logout = QPushButton("Cerrar sesión"); logout.clicked.connect(self._logout); top_layout.addWidget(logout)
        right_layout.addWidget(top); right_layout.addWidget(self.stack, 1); root.addWidget(right, 1)
        self.setCentralWidget(central)
        status = QStatusBar(); status.showMessage("● Conectado a Supabase"); self.setStatusBar(status)
        self._show(0)

    def _subscribe(self) -> None:
        for table in ("product_variants", "orders", "quotations", "embroidery_jobs", "notifications"):
            try: self.service.subscribe(table, lambda payload, t=table: self.bridge.changed.emit(t))
            except Exception: self.statusBar().showMessage("◌ Conectado; Realtime pendiente de reconexión")

    def _realtime_changed(self, table: str) -> None:
        self.statusBar().showMessage(f"● Actualización recibida: {table}", 5000)
        page = self.stack.currentWidget()
        if hasattr(page, "refresh"): page.refresh()

    def _connection_status(self) -> None:
        if self.service.online: self.statusBar().showMessage("● Conectado a Supabase")
        else: self.statusBar().showMessage("● Sin conexión — lectura desde caché; operaciones críticas bloqueadas")

    def _search(self) -> None:
        query = self.global_search.text().strip()
        if len(query) < 2: return
        try:
            rows = self.service.rpc("global_search", {"p_query": query}) or []
            text = "\n".join(f"{r['entity']}: {r['title']} — {r.get('subtitle','')}" for r in rows) or "Sin resultados."
            QMessageBox.information(self, "Resultados de búsqueda", text)
        except Exception as exc: QMessageBox.critical(self, "Búsqueda no disponible", str(exc))

    def _check_updates(self, silent: bool) -> None:
        if not self.updater.configured:
            if not silent:
                QMessageBox.information(self, "Actualizaciones", "Configure GITHUB_REPOSITORY=propietario/repositorio en el archivo .env.")
            return
        if self.update_worker and self.update_worker.isRunning(): return
        self.statusBar().showMessage("Buscando actualizaciones…")
        self.update_worker = UpdateWorker(self.updater)
        self.update_worker.completed.connect(lambda release: self._update_found(release, silent))
        self.update_worker.failed.connect(lambda message: self._update_failed(message, silent))
        self.update_worker.start()

    def _update_found(self, release: ReleaseInfo | None, silent: bool) -> None:
        if not release:
            self.statusBar().showMessage("La aplicación está actualizada", 5000)
            if not silent: QMessageBox.information(self, "Actualizaciones", "Ya tiene la versión más reciente.")
            return
        answer = QMessageBox.question(
            self,
            f"Actualización {release.version} disponible",
            f"Está disponible {release.title}.\n\n¿Desea descargarla e instalarla ahora?",
        )
        if answer != QMessageBox.StandardButton.Yes: return
        self.update_progress = QProgressDialog("Descargando y verificando actualización…", "Cancelar", 0, 0, self)
        self.update_progress.setWindowTitle("Actualización segura"); self.update_progress.setCancelButton(None); self.update_progress.show()
        self.update_worker = UpdateWorker(self.updater, release)
        self.update_worker.completed.connect(self._install_update)
        self.update_worker.failed.connect(lambda message: self._update_failed(message, False))
        self.update_worker.start()

    def _update_failed(self, message: str, silent: bool) -> None:
        if self.update_progress: self.update_progress.close(); self.update_progress = None
        self.statusBar().showMessage("No se pudo consultar la actualización", 5000)
        if not silent: QMessageBox.warning(self, "Actualizaciones", message)

    def _install_update(self, path: object) -> None:
        if self.update_progress: self.update_progress.close(); self.update_progress = None
        installer = str(path)
        if QMessageBox.question(self, "Instalar actualización", "La descarga fue verificada. La aplicación se cerrará para actualizarse. ¿Continuar?") != QMessageBox.StandardButton.Yes:
            return
        started, _pid = QProcess.startDetached(installer, ["/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])
        if not started:
            QMessageBox.critical(self, "Actualización", "Windows no pudo iniciar el instalador.")
            return
        QApplication.quit()

    def _show(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons): button.setChecked(i == index)

    def _toggle_sidebar(self) -> None:
        target = 70 if self.sidebar.width() > 100 else 225
        animation = QPropertyAnimation(self.sidebar, b"maximumWidth", self); animation.setDuration(220); animation.setStartValue(self.sidebar.width()); animation.setEndValue(target); animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.sidebar.setMinimumWidth(target); self._sidebar_animation = animation; animation.start()

    def _theme(self) -> None:
        self.dark = not self.dark; QApplication.instance().setStyleSheet(stylesheet("dark" if self.dark else "light"))

    def _logout(self) -> None:
        if QMessageBox.question(self, "Cerrar sesión", "¿Desea cerrar la sesión actual?") != QMessageBox.StandardButton.Yes: return
        self.service.sign_out()
        from ui.login_window import LoginWindow
        self.login_window = LoginWindow(self.service); self.login_window.show(); self.close()

