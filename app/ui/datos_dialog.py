"""
Previsualización de los datos ya cargados de una fuente.

Equivale a `DatosModal.tsx`. Lee el Parquet de destino y lo muestra en una tabla
virtualizada, con búsqueda global. Sirve para que el auditor confirme que el
archivo que subió es el correcto antes de generar el hallazgo.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QTableView, QVBoxLayout, QWidget,
)

from app.catalog.fuentes import Slot
from app.storage.files import leer_datos
from app.tasks.runner import POOL, Tarea
from app.ui.table_model import DataFrameModel


class DatosDialog(QDialog):
    def __init__(self, slot: Slot, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.slot = slot
        self.setWindowTitle(f"Datos cargados · {slot.display_label}")
        self.resize(1100, 680)

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
        self.buscador.textChanged.connect(self._filtrar)
        cabecera.addWidget(self.buscador)
        raiz.addLayout(cabecera)

        self.resumen = QLabel("Cargando…")
        self.resumen.setObjectName("CardMeta")
        raiz.addWidget(self.resumen)

        self.modelo = DataFrameModel()
        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setAlternatingRowColors(False)
        self.tabla.setSelectionBehavior(QTableView.SelectRows)
        self.tabla.verticalHeader().setDefaultSectionSize(30)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla.horizontalHeader().setStretchLastSection(True)
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
        tarea.senales.ok.connect(self._al_cargar)
        tarea.senales.error.connect(lambda m: self.resumen.setText(f"Error: {m}"))
        POOL.start(tarea)

    def _al_cargar(self, df) -> None:
        self.modelo.set_dataframe(df)
        self._actualizar_resumen()
        self.tabla.resizeColumnsToContents()
        for col in range(self.modelo.columnCount()):
            if self.tabla.columnWidth(col) > 320:
                self.tabla.setColumnWidth(col, 320)

    def _filtrar(self, texto: str) -> None:
        self.modelo.aplicar_filtro(texto)
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
