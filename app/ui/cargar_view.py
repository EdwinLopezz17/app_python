"""
Pantalla "Cargar Información" de UN hallazgo.

Muestra exactamente las fuentes que ese hallazgo necesita, agrupadas
(Aplicaciones / Otros Reportes / Bases de Datos), con un indicador de progreso
arriba. Cuando están todas cargadas, el hallazgo queda listo para generarse.

Se instancia una por hallazgo. La lista de fuentes viene del catálogo, no está
escrita aquí: agregar o quitar una fuente de un hallazgo es editar
`app/catalog/hallazgos.py`, no esta vista.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from app.catalog.fuentes import APLICACIONES, BASES_DE_DATOS, OTROS_REPORTES, Fuente
from app.catalog.hallazgos import Hallazgo
from app.storage.files import estado_slot, eliminar_fuente
from app.ui.datos_dialog import DatosDialog
from app.ui.fuente_card import FuenteCard
from app.ui.panel_estado import PanelEstado

COLUMNAS_GRID = 3
ORDEN_GRUPOS = [OTROS_REPORTES, BASES_DE_DATOS, APLICACIONES]


class CargarView(QWidget):
    """Vista de carga de un hallazgo concreto."""

    progreso_cambiado = Signal(str, int, int)  # hallazgo_id, cargadas, total
    ir_hallazgo = Signal(str)                  # pasar a generar el hallazgo
    ir_inicio = Signal()

    def __init__(self, hallazgo: Hallazgo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hallazgo = hallazgo
        self.setObjectName("Canvas")

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        raiz.addWidget(self._construir_cabecera())

        # Fila principal: cards a la izquierda, panel de estado a la derecha.
        fila_principal = QWidget()
        fila_principal.setObjectName("Canvas")
        columnas = QHBoxLayout(fila_principal)
        columnas.setContentsMargins(0, 0, 0, 0)
        columnas.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        contenido.setObjectName("Canvas")
        self._cuerpo = QVBoxLayout(contenido)
        self._cuerpo.setContentsMargins(24, 20, 24, 32)
        self._cuerpo.setSpacing(24)

        self.cards: list[FuenteCard] = []
        self._construir_grupos()
        self._cuerpo.addStretch(1)

        scroll.setWidget(contenido)
        self._scroll = scroll
        columnas.addWidget(scroll, 1)

        self.panel = PanelEstado(hallazgo)
        self.panel.cerrar.connect(self._alternar_panel)
        self.panel.ir_a_slot.connect(self._ir_a_slot)
        columnas.addWidget(self.panel)

        raiz.addWidget(fila_principal, 1)

        self.refrescar()

    # ── construcción ───────────────────────────────────────────────────────
    def _construir_cabecera(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("TopBar")
        layout = QVBoxLayout(barra)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(4)

        breadcrumb = QLabel(
            f"{self.hallazgo.cert_label}  ›  {self.hallazgo.label}  ›  Cargar Información"
        )
        breadcrumb.setObjectName("Breadcrumb")
        layout.addWidget(breadcrumb)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        btn_volver = QPushButton("← Inicio")
        btn_volver.setProperty("variante", "ghost")
        btn_volver.clicked.connect(self.ir_inicio.emit)
        fila.addWidget(btn_volver)

        titulo = QLabel("Cargar Información")
        titulo.setObjectName("Titulo")
        fila.addWidget(titulo)
        fila.addStretch(1)

        self.lbl_progreso = QLabel()
        self.lbl_progreso.setObjectName("Badge")
        self.lbl_progreso.setProperty("tono", "pendiente")
        fila.addWidget(self.lbl_progreso)

        self.btn_panel = QPushButton("Ocultar estado")
        self.btn_panel.setProperty("variante", "ghost")
        self.btn_panel.setToolTip(
            "Muestra u oculta el panel que verifica, leyendo el disco, qué "
            "archivos están realmente guardados."
        )
        self.btn_panel.clicked.connect(self._alternar_panel)
        fila.addWidget(self.btn_panel)

        btn_limpiar = QPushButton("Eliminar todo")
        btn_limpiar.setProperty("variante", "peligro")
        btn_limpiar.clicked.connect(self._eliminar_todo)
        fila.addWidget(btn_limpiar)

        self.btn_generar = QPushButton("Ir a Hallazgos →")
        self.btn_generar.clicked.connect(
            lambda: self.ir_hallazgo.emit(self.hallazgo.id)
        )
        fila.addWidget(self.btn_generar)

        layout.addLayout(fila)

        if self.hallazgo.descripcion:
            desc = QLabel(self.hallazgo.descripcion)
            desc.setObjectName("Breadcrumb")
            layout.addWidget(desc)

        return barra

    def _construir_grupos(self) -> None:
        por_grupo: dict[str, list[Fuente]] = {}
        for fuente in self.hallazgo.fuentes:
            por_grupo.setdefault(fuente.group, []).append(fuente)

        for grupo in ORDEN_GRUPOS:
            fuentes = por_grupo.get(grupo)
            if not fuentes:
                continue

            titulo = QLabel(f"{grupo.upper()}  ·  {len(fuentes)}")
            titulo.setObjectName("Seccion")
            self._cuerpo.addWidget(titulo)

            contenedor = QFrame()
            contenedor.setObjectName("Canvas")
            grid = QGridLayout(contenedor)
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(16)
            grid.setVerticalSpacing(16)

            for indice, fuente in enumerate(fuentes):
                card = FuenteCard(fuente)
                card.cambiado.connect(self.refrescar)
                card.ver_datos.connect(self._abrir_datos)
                grid.addWidget(card, indice // COLUMNAS_GRID, indice % COLUMNAS_GRID)
                self.cards.append(card)

            for col in range(COLUMNAS_GRID):
                grid.setColumnStretch(col, 1)

            self._cuerpo.addWidget(contenedor)

    # ── estado ─────────────────────────────────────────────────────────────
    def refrescar(self) -> None:
        for card in self.cards:
            card.refrescar()
        if hasattr(self, "panel") and self.panel.isVisible():
            self.panel.refrescar()

        slots = [s for f in self.hallazgo.fuentes for s in f.slots]
        cargados = sum(1 for s in slots if estado_slot(s).existe)
        total = len(slots)

        self.lbl_progreso.setText(f"{cargados} / {total} archivos cargados")
        completo = cargados == total and total > 0
        self.btn_generar.setEnabled(completo)
        self.btn_generar.setToolTip(
            "" if completo else f"Faltan {total - cargados} archivo(s) por cargar."
        )
        self.lbl_progreso.setProperty("tono", "ok" if cargados == total else "pendiente")
        self.lbl_progreso.style().unpolish(self.lbl_progreso)
        self.lbl_progreso.style().polish(self.lbl_progreso)

        self.progreso_cambiado.emit(self.hallazgo.id, cargados, total)

    def _alternar_panel(self) -> None:
        visible = not self.panel.isVisible()
        self.panel.setVisible(visible)
        self.btn_panel.setText("Ocultar estado" if visible else "Ver estado")
        if visible:
            self.panel.refrescar()

    def _ir_a_slot(self, file_name: str) -> None:
        """Desplaza la vista hasta la card que contiene ese archivo."""
        for card in self.cards:
            for fila in card.filas:
                if fila.slot.key == file_name:
                    self._scroll.ensureWidgetVisible(card, 0, 60)
                    return

    def _abrir_datos(self, slot) -> None:
        DatosDialog(slot, self).exec()

    def _eliminar_todo(self) -> None:
        respuesta = QMessageBox.warning(
            self, "Eliminar todos los archivos",
            "Se eliminarán TODOS los archivos cargados de este hallazgo.\n\n"
            "Varias de estas fuentes son compartidas: eliminarlas aquí también "
            "las quita de los demás hallazgos que dependen de ellas.\n\n"
            "¿Continuar?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if respuesta != QMessageBox.Yes:
            return
        for fuente in self.hallazgo.fuentes:
            eliminar_fuente(fuente)
        self.refrescar()
