from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from app.catalog.fuentes import APLICACIONES, BASES_DE_DATOS, OTROS_REPORTES, Fuente
from app.catalog.hallazgos import Hallazgo
from app.storage import purge
from app.storage.files import estado_slot
from app.ui.datos_dialog import DatosDialog
from app.ui.fuente_card import FuenteCard
from app.ui.panel_estado import PanelEstado
from app.ui.responsive import ANCHO_MIN_CARD, ContenedorFlow, GridResponsivo

ORDEN_GRUPOS = [OTROS_REPORTES, BASES_DE_DATOS, APLICACIONES]

#: Debajo de este ancho útil, el panel de estado se esconde solo para que las
#: cards recuperen una segunda columna. El usuario puede forzarlo igual.
UMBRAL_PANEL = 980


class CargarView(QWidget):
    progreso_cambiado = Signal(str, int, int)
    ir_hallazgo = Signal(str)
    ir_inicio = Signal()

    def __init__(self, hallazgo: Hallazgo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hallazgo = hallazgo
        self.setObjectName("Canvas")

        # None = automático según el ancho. True/False = el usuario decidió.
        self._panel_forzado: bool | None = None

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        raiz.addWidget(self._construir_cabecera())

        fila_principal = QWidget()
        fila_principal.setObjectName("Canvas")
        columnas = QHBoxLayout(fila_principal)
        columnas.setContentsMargins(0, 0, 0, 0)
        columnas.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        contenido = QWidget()
        contenido.setObjectName("Canvas")
        self._cuerpo = QVBoxLayout(contenido)
        self._cuerpo.setContentsMargins(24, 20, 24, 32)
        self._cuerpo.setSpacing(24)

        self.cards: list[FuenteCard] = []
        self._grids: list[GridResponsivo] = []
        self._construir_grupos()
        self._cuerpo.addStretch(1)

        scroll.setWidget(contenido)
        self._scroll = scroll
        # Equivalente de `min-w-0 flex-1`: la columna de cards puede encogerse,
        # así nunca empuja al panel por encima de ella.
        scroll.setMinimumWidth(0)
        scroll.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        columnas.addWidget(scroll, 1)

        self.panel = PanelEstado(hallazgo)
        self.panel.cerrar.connect(self._ocultar_panel)
        self.panel.ir_a_slot.connect(self._ir_a_slot)
        columnas.addWidget(self.panel, 0)

        raiz.addWidget(fila_principal, 1)

        self.refrescar()

    # ------------------------------------------------------------------
    # Cabecera
    # ------------------------------------------------------------------

    def _construir_cabecera(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("TopBar")
        layout = QVBoxLayout(barra)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(8)

        breadcrumb = QLabel(
            f"{self.hallazgo.cert_label}  ›  {self.hallazgo.label}  ›  Cargar Información"
        )
        breadcrumb.setObjectName("Breadcrumb")
        breadcrumb.setWordWrap(True)
        layout.addWidget(breadcrumb)

        titulo_fila = QHBoxLayout()
        titulo_fila.setSpacing(10)

        btn_volver = QPushButton("←  Inicio")
        btn_volver.setProperty("variante", "ghost")
        btn_volver.setCursor(Qt.PointingHandCursor)
        btn_volver.setToolTip("Volver a la pantalla de certificaciones")
        btn_volver.clicked.connect(self.ir_inicio.emit)
        titulo_fila.addWidget(btn_volver)

        titulo = QLabel("Cargar Información")
        titulo.setObjectName("Titulo")
        titulo_fila.addWidget(titulo)

        self.lbl_progreso = QLabel()
        self.lbl_progreso.setObjectName("Badge")
        self.lbl_progreso.setProperty("tono", "pendiente")
        titulo_fila.addWidget(self.lbl_progreso)
        titulo_fila.addStretch(1)
        layout.addLayout(titulo_fila)

        # Los botones bajan de línea solos cuando la ventana está a media
        # pantalla, en vez de recortarse.
        acciones = ContenedorFlow(espacio_h=8, espacio_v=8)

        btn_limpiar = QPushButton("Eliminar todo")
        btn_limpiar.setProperty("variante", "ghost")
        btn_limpiar.setProperty("tono", "peligro")
        btn_limpiar.setCursor(Qt.PointingHandCursor)
        btn_limpiar.setToolTip(
            "Elimina los archivos ya cargados de este hallazgo o de toda la "
            "certificación. Pide confirmación."
        )
        btn_limpiar.clicked.connect(self._eliminar_todo)
        acciones.agregar(btn_limpiar)

        self.btn_panel = QPushButton("Ocultar estado de archivos")
        self.btn_panel.setProperty("variante", "ghost")
        self.btn_panel.setCursor(Qt.PointingHandCursor)
        self.btn_panel.setToolTip(
            "Muestra u oculta el panel lateral que verifica, leyendo el disco, "
            "qué archivos están realmente guardados."
        )
        self.btn_panel.clicked.connect(self._alternar_panel)
        acciones.agregar(self.btn_panel)

        self.btn_generar = QPushButton("Generar Hallazgos  →")
        self.btn_generar.setCursor(Qt.PointingHandCursor)
        self.btn_generar.clicked.connect(
            lambda: self.ir_hallazgo.emit(self.hallazgo.id)
        )
        acciones.agregar(self.btn_generar)

        layout.addWidget(acciones)

        if self.hallazgo.descripcion:
            desc = QLabel(self.hallazgo.descripcion)
            desc.setObjectName("Breadcrumb")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        return barra

    # ------------------------------------------------------------------
    # Cuerpo
    # ------------------------------------------------------------------

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

            grid = GridResponsivo(ancho_min=ANCHO_MIN_CARD, espacio=16, max_columnas=3)
            for fuente in fuentes:
                card = FuenteCard(fuente)
                card.cambiado.connect(self.refrescar)
                card.ver_datos.connect(self._abrir_datos)
                grid.agregar(card)
                self.cards.append(card)

            self._grids.append(grid)
            self._cuerpo.addWidget(grid)

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    def refrescar(self) -> None:
        for card in self.cards:
            card.refrescar()
        if hasattr(self, "panel") and self.panel.isVisible():
            self.panel.refrescar()

        slots = [s for f in self.hallazgo.fuentes for s in f.slots]
        cargados = sum(1 for s in slots if estado_slot(s).existe)
        total = len(slots)
        faltan = total - cargados
        completo = faltan == 0 and total > 0

        self.lbl_progreso.setText(f"{cargados} / {total} archivos cargados")
        self.lbl_progreso.setProperty("tono", "ok" if completo else "pendiente")
        self.lbl_progreso.style().unpolish(self.lbl_progreso)
        self.lbl_progreso.style().polish(self.lbl_progreso)

        # El propio botón dice por qué no se puede, en vez de quedar gris y
        # mudo con la explicación escondida en un tooltip.
        self.btn_generar.setEnabled(completo)
        if completo:
            self.btn_generar.setText("Generar Hallazgos  →")
            self.btn_generar.setToolTip(
                "Todas las fuentes están cargadas. Ir a la pantalla de hallazgos."
            )
        else:
            plural = "archivos" if faltan != 1 else "archivo"
            self.btn_generar.setText(f"Faltan {faltan} {plural}")
            self.btn_generar.setToolTip(
                f"Carga los {faltan} {plural} que faltan para poder generar."
            )

        self.progreso_cambiado.emit(self.hallazgo.id, cargados, total)

    # ------------------------------------------------------------------
    # Panel lateral
    # ------------------------------------------------------------------

    def _aplicar_panel(self, visible: bool) -> None:
        self.panel.setVisible(visible)
        self.btn_panel.setText(
            "Ocultar estado de archivos" if visible else "Ver estado de archivos"
        )
        if visible:
            self.panel.refrescar()

    def _alternar_panel(self) -> None:
        self._panel_forzado = not self.panel.isVisible()
        self._aplicar_panel(self._panel_forzado)

    def _ocultar_panel(self) -> None:
        self._panel_forzado = False
        self._aplicar_panel(False)

    def _panel_automatico(self) -> None:
        if self._panel_forzado is None:
            self._aplicar_panel(self.width() >= UMBRAL_PANEL)

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._panel_automatico()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._panel_automatico()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _ir_a_slot(self, file_name: str) -> None:
        for card in self.cards:
            for fila in card.filas:
                if fila.slot.key == file_name:
                    self._scroll.ensureWidgetVisible(card, 0, 60)
                    return

    def _abrir_datos(self, slot) -> None:
        DatosDialog(slot, self).exec()

    def _eliminar_todo(self) -> None:
        dialogo = QMessageBox(self)
        dialogo.setIcon(QMessageBox.Warning)
        dialogo.setWindowTitle("Eliminar información cargada")
        dialogo.setText("¿Qué alcance quieres eliminar?")

        compartidas = purge.fuentes_compartidas(self.hallazgo)
        detalle = (
            f"«Este hallazgo» elimina los archivos de {self.hallazgo.label} y su "
            "resultado generado.\n\n"
            f"«Toda la certificación» elimina los archivos de TODOS los hallazgos "
            f"de {self.hallazgo.cert_label} y todos sus resultados generados.\n\n"
            "Esta acción no se puede deshacer."
        )
        if compartidas:
            detalle += (
                "\n\nFuentes compartidas con otros hallazgos que también "
                "quedarán sin cargar:\n· " + "\n· ".join(compartidas)
            )
        dialogo.setInformativeText(detalle)

        dialogo.addButton(
            f"Este hallazgo ({self.hallazgo.label})", QMessageBox.DestructiveRole
        )
        btn_cert = dialogo.addButton(
            "Toda la certificación", QMessageBox.DestructiveRole
        )
        btn_cancelar = dialogo.addButton("Cancelar", QMessageBox.RejectRole)
        dialogo.setDefaultButton(btn_cancelar)
        dialogo.exec()

        elegido = dialogo.clickedButton()
        if elegido is btn_cancelar or elegido is None:
            return

        if elegido is btn_cert:
            resultado = purge.borrar_certificacion(self.hallazgo.cert_id)
        else:
            resultado = purge.borrar_hallazgo(self.hallazgo)

        self.refrescar()
        QMessageBox.information(
            self, "Eliminar información cargada", resultado.mensaje()
        )
