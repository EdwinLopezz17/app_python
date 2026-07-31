from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtWidgets import (
    QCalendarWidget, QDateEdit, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QTableView, QVBoxLayout, QWidget,
)

from app.cache import store
from app.cache.store import EstadoCache
from app.catalog import display
from app.catalog.hallazgos import Hallazgo
from app.exports import excel
from app.generation import reports
from app.storage.files import estado_slot
from app.tasks.runner import POOL, Tarea
from app.ui.table_model import DataFrameModel

BANDERAS_KPI = [
    "is_cesado_activo", "is_login_post_cese", "is_no_identificado",
    "is_sin_uso_90d", "is_deshabilitado_180d", "is_no_cesado_oportunamente",
]


class HallazgoView(QWidget):

    ir_cargar = Signal(str)
    cambiado = Signal()

    def __init__(self, hallazgo: Hallazgo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hallazgo = hallazgo
        self._generando = False
        self.setObjectName("Canvas")

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        raiz.addWidget(self._cabecera())

        cuerpo = QWidget()
        cuerpo.setObjectName("Canvas")
        layout = QVBoxLayout(cuerpo)
        layout.setContentsMargins(24, 16, 24, 20)
        layout.setSpacing(12)

        self.aviso = QLabel()
        self.aviso.setObjectName("Badge")
        self.aviso.setWordWrap(True)
        self.aviso.hide()
        layout.addWidget(self.aviso)

        self.barra = QProgressBar()
        self.barra.setRange(0, 0)
        self.barra.hide()
        layout.addWidget(self.barra)

        self.kpis = QWidget()
        self.kpis.setObjectName("Canvas")
        self._kpis_layout = QHBoxLayout(self.kpis)
        self._kpis_layout.setContentsMargins(0, 0, 0, 0)
        self._kpis_layout.setSpacing(12)
        self.kpis.hide()
        layout.addWidget(self.kpis)

        self.modelo = DataFrameModel()
        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setSelectionBehavior(QTableView.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(30)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabla, 1)

        raiz.addWidget(cuerpo, 1)
        self.refrescar()

    def _cabecera(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("TopBar")
        layout = QVBoxLayout(barra)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)

        breadcrumb = QLabel(
            f"{self.hallazgo.cert_label}  ›  {self.hallazgo.label}  ›  Hallazgos"
        )
        breadcrumb.setObjectName("Breadcrumb")
        layout.addWidget(breadcrumb)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        titulo = QLabel(self.hallazgo.label)
        titulo.setObjectName("Titulo")
        fila.addWidget(titulo)

        self.estado_badge = QLabel()
        self.estado_badge.setObjectName("Badge")
        fila.addWidget(self.estado_badge)
        fila.addStretch(1)

        etiqueta_fecha = QLabel("Fecha de corte")
        etiqueta_fecha.setObjectName("CardMeta")
        fila.addWidget(etiqueta_fecha)

        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd MMM yyyy")
        self.fecha.setDate(QDate.currentDate())
        self.fecha.setMinimumDate(QDate(2020, 1, 1))
        self.fecha.setMaximumDate(QDate.currentDate().addYears(1))
        self.fecha.setToolTip(
            "Fecha de referencia para los cálculos de días sin uso y cese oportuno."
        )
        self.fecha.calendarWidget().setGridVisible(False)
        self.fecha.calendarWidget().setVerticalHeaderFormat(
            QCalendarWidget.NoVerticalHeader
        )
        fila.addWidget(self.fecha)

        btn_hoy = QPushButton("Hoy")
        btn_hoy.setProperty("variante", "ghost")
        btn_hoy.setToolTip("Usar la fecha actual")
        btn_hoy.clicked.connect(lambda: self.fecha.setDate(QDate.currentDate()))
        fila.addWidget(btn_hoy)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar…")
        self.buscador.setFixedWidth(200)
        self.buscador.textChanged.connect(self._filtrar)
        fila.addWidget(self.buscador)

        self.btn_cargar = QPushButton("Cargar Información")
        self.btn_cargar.setProperty("variante", "ghost")
        self.btn_cargar.clicked.connect(lambda: self.ir_cargar.emit(self.hallazgo.id))
        fila.addWidget(self.btn_cargar)

        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setProperty("variante", "ghost")
        self.btn_exportar.clicked.connect(self._exportar)
        fila.addWidget(self.btn_exportar)

        self.btn_generar = QPushButton("Generar")
        self.btn_generar.clicked.connect(self._generar)
        fila.addWidget(self.btn_generar)

        layout.addLayout(fila)
        return barra

    def refrescar(self) -> None:
        if self._generando:
            return

        slots = [s for f in self.hallazgo.fuentes for s in f.slots]
        faltantes = [s for s in slots if not estado_slot(s).existe]
        conectado = reports.disponible(self.hallazgo.id)

        self.btn_generar.setEnabled(conectado and not faltantes)
        if not conectado:
            self.btn_generar.setToolTip("Este hallazgo aún no está conectado a su reporte.")
        elif faltantes:
            self.btn_generar.setToolTip(f"Faltan {len(faltantes)} archivo(s) por cargar.")
        else:
            self.btn_generar.setToolTip("")

        estado = store.estado(self.hallazgo) if conectado else EstadoCache.AUSENTE
        meta = store.leer_meta(self.hallazgo)

        if not conectado:
            self._badge("NO DISPONIBLE", "pendiente")
            self._mostrar_aviso(
                "La generación de este hallazgo todavía no está conectada a su "
                "reporte en logic/.", "aviso")
        elif faltantes:
            self._badge("FALTAN FUENTES", "aviso")
            nombres = ", ".join(s.display_label for s in faltantes[:4])
            if len(faltantes) > 4:
                nombres += f" y {len(faltantes) - 4} más"
            self._mostrar_aviso(
                f"Faltan {len(faltantes)} de {len(slots)} archivos: {nombres}. "
                "Usa «Cargar Información» para completarlos.", "aviso")
        elif estado is EstadoCache.DESACTUALIZADA:
            self._badge("DESACTUALIZADO", "aviso")
            self.btn_generar.setText("Regenerar")
            self._mostrar_aviso(
                "Las fuentes cambiaron desde la última generación. "
                "Los datos mostrados corresponden a la ejecución anterior.", "aviso")
        elif estado is EstadoCache.VIGENTE and meta:
            self._badge("VIGENTE", "ok")
            self.btn_generar.setText("Regenerar")
            self.aviso.hide()
        else:
            self._badge("SIN GENERAR", "pendiente")
            self.btn_generar.setText("Generar")
            self.aviso.hide()

        if conectado and estado is not EstadoCache.AUSENTE and self.modelo.total_original == 0:
            self._cargar_cache()

        self.btn_exportar.setEnabled(self.modelo.total_original > 0)

    def _badge(self, texto: str, tono: str) -> None:
        self.estado_badge.setText(texto)
        self.estado_badge.setProperty("tono", tono)
        self.estado_badge.style().unpolish(self.estado_badge)
        self.estado_badge.style().polish(self.estado_badge)

    def _mostrar_aviso(self, texto: str, tono: str) -> None:
        self.aviso.setText(texto)
        self.aviso.setProperty("tono", tono)
        self.aviso.style().unpolish(self.aviso)
        self.aviso.style().polish(self.aviso)
        self.aviso.show()

    def _generar(self) -> None:
        self._generando = True
        self.btn_generar.setEnabled(False)
        self.btn_exportar.setEnabled(False)
        self.barra.show()
        self._badge("GENERANDO…", "aviso")
        self._mostrar_aviso(
            "Procesando las fuentes. Esto puede tardar varios minutos según el "
            "volumen de datos.", "aviso")

        fecha_ref: date = self.fecha.date().toPython()
        tarea = Tarea(reports.generar, self.hallazgo.id, fecha_ref)
        tarea.senales.ok.connect(self._al_generar)
        tarea.senales.error.connect(self._al_fallar)
        POOL.start(tarea)

    def _al_generar(self, df) -> None:
        self._generando = False
        self.barra.hide()
        try:
            store.guardar(self.hallazgo, df)
        except Exception as exc:
            self._al_fallar(f"El hallazgo se generó pero no se pudo guardar: {exc}")
            return
        self._pintar(df)
        self.refrescar()
        self.cambiado.emit()

    def _al_fallar(self, mensaje: str) -> None:
        self._generando = False
        self.barra.hide()
        self._badge("ERROR", "error")
        self._mostrar_aviso(f"No se pudo generar el hallazgo: {mensaje}", "error")
        self.btn_generar.setEnabled(True)

    def _cargar_cache(self) -> None:
        resultado = store.cargar(self.hallazgo)
        if resultado.df is not None:
            self._pintar(resultado.df)

    def _pintar(self, df) -> None:
        self.modelo.set_dataframe(df, self.hallazgo.modelo)
        self.buscador.clear()
        self._construir_kpis(df)
        self.tabla.resizeColumnsToContents()
        for col in range(self.modelo.columnCount()):
            if self.tabla.columnWidth(col) > 300:
                self.tabla.setColumnWidth(col, 300)
        self.btn_exportar.setEnabled(len(df) > 0)

    def _construir_kpis(self, df) -> None:
        while self._kpis_layout.count():
            item = self._kpis_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        etiquetas = display.etiquetas(self.hallazgo.modelo) if self.hallazgo.modelo else {}
        tarjetas = [("Total de filas", len(df))]
        for campo in BANDERAS_KPI:
            if campo in df.columns:
                try:
                    conteo = int(df[campo].astype(bool).sum())
                except Exception:
                    continue
                tarjetas.append((etiquetas.get(campo, campo), conteo))

        for etiqueta, valor in tarjetas:
            tarjeta = QFrame()
            tarjeta.setObjectName("KpiCard")
            interno = QVBoxLayout(tarjeta)
            interno.setContentsMargins(14, 10, 14, 10)
            interno.setSpacing(0)

            numero = QLabel(f"{valor:,}".replace(",", " "))
            numero.setObjectName("Kpi")
            interno.addWidget(numero)

            desc = QLabel(etiqueta.upper())
            desc.setObjectName("KpiEtiqueta")
            desc.setWordWrap(True)
            interno.addWidget(desc)

            self._kpis_layout.addWidget(tarjeta)

        self._kpis_layout.addStretch(1)
        self.kpis.setVisible(bool(tarjetas))

    def _filtrar(self, texto: str) -> None:
        self.modelo.aplicar_filtro(texto)

    def _exportar(self) -> None:
        df = self.modelo.dataframe
        if df is None or df.empty:
            QMessageBox.information(self, "Exportar", "No hay datos para exportar.")
            return

        destino, _ = QFileDialog.getSaveFileName(
            self, "Exportar hallazgo",
            excel.nombre_sugerido(self.hallazgo.id),
            "Excel (*.xlsx)",
        )
        if not destino:
            return

        self.btn_exportar.setEnabled(False)
        self.btn_exportar.setText("Exportando…")

        tarea = Tarea(excel.exportar, df, destino, self.hallazgo.modelo)
        tarea.senales.ok.connect(self._al_exportar)
        tarea.senales.error.connect(
            lambda m: QMessageBox.critical(self, "Exportar", f"No se pudo exportar: {m}")
        )
        tarea.senales.terminada.connect(lambda: (
            self.btn_exportar.setEnabled(True),
            self.btn_exportar.setText("Exportar Excel"),
        ))
        POOL.start(tarea)

    def _al_exportar(self, ruta) -> None:
        filtradas = len(self.modelo.dataframe)
        total = self.modelo.total_original
        detalle = "" if filtradas == total else f"\n\nSe exportaron las {filtradas} filas filtradas."
        QMessageBox.information(
            self, "Exportación completa", f"Archivo guardado en:\n{ruta}{detalle}"
        )
