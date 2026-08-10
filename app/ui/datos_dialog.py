from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QTableView, QVBoxLayout, QWidget,
)

from app.catalog.fuentes import Slot
from app.storage.files import leer_datos
from app.tasks.runner import POOL, Tarea
from app.ui import preferencias
from app.ui.table_model import DataFrameModel


class DatosDialog(QDialog):
    def __init__(self, slot: Slot, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.slot = slot
        self._vivo = True
        self._senales = None
        self.setWindowTitle(f"Datos cargados · {slot.display_label}")
        tamano = preferencias.leer_tamano_dialogo()
        self.resize(*tamano) if tamano else self.resize(1100, 680)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 18, 20, 18)
        raiz.setSpacing(12)

        cabecera = QHBoxLayout()
        titulo = QLabel(slot.display_label)
        titulo.setObjectName("Titulo")
        cabecera.addWidget(titulo)
        cabecera.addStretch(1)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar en todas las columnas…")
        self.buscador.setFixedWidth(280)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self._aplicar_filtro)
        self.buscador.textChanged.connect(lambda _: self._debounce.start())
        cabecera.addWidget(self.buscador)
        raiz.addLayout(cabecera)

        self.resumen = QLabel("Cargando…")
        self.resumen.setObjectName("CardMeta")
        raiz.addWidget(self.resumen)

        self.modelo = DataFrameModel()
        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(True)
        self.tabla.setSelectionBehavior(QTableView.SelectRows)
        self.tabla.verticalHeader().setDefaultSectionSize(30)
        self.tabla.verticalHeader().setVisible(False)
        encabezado = self.tabla.horizontalHeader()
        encabezado.setSectionResizeMode(QHeaderView.Interactive)
        encabezado.setStretchLastSection(True)
        encabezado.setHighlightSections(False)
        encabezado.setMinimumSectionSize(90)
        encabezado.setFixedHeight(38)
        encabezado.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._encabezado = encabezado
        self.tabla.setSortingEnabled(False)
        raiz.addWidget(self.tabla, 1)

        pie = QHBoxLayout()
        pie.addStretch(1)
        cerrar = QPushButton("Cerrar")
        cerrar.clicked.connect(self.accept)
        pie.addWidget(cerrar)
        raiz.addLayout(pie)

        self._cargar()

    def _cargar(self) -> None:
        tarea = Tarea(leer_datos, self.slot)
        self._senales = tarea.senales
        tarea.senales.ok.connect(self._al_cargar)
        tarea.senales.error.connect(self._al_fallar)
        POOL.start(tarea)

    def _guardar_preferencias(self) -> None:
        preferencias.guardar_tamano_dialogo(self.width(), self.height())
        columnas = self.modelo.columnCount()
        if columnas:
            preferencias.guardar_columnas(
                self.slot.key,
                [self.tabla.columnWidth(col) for col in range(columnas)],
            )

    def _desconectar(self) -> None:
        self._vivo = False
        if self._senales is None:
            return
        try:
            self._senales.ok.disconnect(self._al_cargar)
            self._senales.error.disconnect(self._al_fallar)
        except (RuntimeError, TypeError):
            pass
        self._senales = None

    def closeEvent(self, evento) -> None:
        self._guardar_preferencias()
        self._desconectar()
        super().closeEvent(evento)

    def done(self, resultado: int) -> None:
        if self._vivo:
            self._guardar_preferencias()
        self._desconectar()
        super().done(resultado)

    def _al_fallar(self, mensaje: str) -> None:
        if not self._vivo:
            return
        self.resumen.setText(f"Error: {mensaje}")

    def _al_cargar(self, df) -> None:
        if not self._vivo:
            return
        self.modelo.set_dataframe(df)
        self._actualizar_resumen()

        guardados = preferencias.leer_columnas(self.slot.key)
        if len(guardados) == self.modelo.columnCount():
            for col, ancho in enumerate(guardados):
                self.tabla.setColumnWidth(col, ancho)
            return

        self._encabezado.setResizeContentsPrecision(200)
        self.tabla.resizeColumnsToContents()
        for col in range(self.modelo.columnCount()):
            if self.tabla.columnWidth(col) > 320:
                self.tabla.setColumnWidth(col, 320)

    def _aplicar_filtro(self) -> None:
        if not self._vivo:
            return
        self.modelo.aplicar_filtro(self.buscador.text())
        self._actualizar_resumen()

    def _actualizar_resumen(self) -> None:
        visibles = self.modelo.rowCount()
        total = self.modelo.total_original
        columnas = self.modelo.columnCount()
        if visibles == total:
            self.resumen.setText(f"{total:,} filas · {columnas} columnas".replace(",", " "))
        else:
            self.resumen.setText(
                f"{visibles:,} de {total:,} filas · {columnas} columnas".replace(",", " ")
            )
