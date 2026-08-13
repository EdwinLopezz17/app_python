from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from app.catalog.fuentes import APLICACIONES, BASES_DE_DATOS, OTROS_REPORTES, Fuente
from app.catalog.hallazgos import Hallazgo
from app.storage import purge
from app.storage.files import estado_slot
from app.ui.datos_dialog import DatosDialog
from app.ui.fuente_card import FuenteCard
from app.ui import preferencias
from app.ui.panel_estado import PanelEstado
from app.ui.responsive import (
    ANCHO_MAX_CARD, ANCHO_MIN_CARD, MAX_COLUMNAS_CARD, ContenedorFlow,
    GridResponsivo,
)

ORDEN_GRUPOS = [OTROS_REPORTES, BASES_DE_DATOS, APLICACIONES]

UMBRAL_PANEL = 980

FILTROS = [
    ("todas", "Todas"),
    ("", "Pendientes"),
    ("error", "Con error"),
    ("cargado", "Cargadas"),
]


class CargarView(QWidget):
    progreso_cambiado = Signal(str, int, int)
    ir_hallazgo = Signal(str)
    ir_inicio = Signal()

    def __init__(self, hallazgo: Hallazgo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hallazgo = hallazgo
        self.setObjectName("Canvas")

        self._panel_forzado: bool | None = preferencias.leer_panel()
        self._sobre_umbral = True

        self._en_curso = 0

        self._filtro_estado = "todas"
        self._busqueda = ""
        self._secciones: list[tuple[QLabel, GridResponsivo]] = []

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

        self.sin_resultados = QLabel(
            "Ninguna fuente coincide con el filtro."
        )
        self.sin_resultados.setObjectName("SinResultados")
        self.sin_resultados.setAlignment(Qt.AlignCenter)
        self.sin_resultados.hide()
        self._cuerpo.addWidget(self.sin_resultados)

        self._cuerpo.addStretch(1)

        scroll.setWidget(contenido)
        self._scroll = scroll
        scroll.setMinimumWidth(0)
        scroll.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        columnas.addWidget(scroll, 1)

        self.panel = PanelEstado(hallazgo)
        self.panel.cerrar.connect(self._ocultar_panel)
        self.panel.ir_a_slot.connect(self._ir_a_slot)
        columnas.addWidget(self.panel, 0)

        raiz.addWidget(fila_principal, 1)

        self._registrar_atajos()
        self.refrescar()

    def _registrar_atajos(self) -> None:
        buscar = QShortcut(QKeySequence.Find, self)
        buscar.activated.connect(self._enfocar_buscador)

        limpiar = QShortcut(QKeySequence(Qt.Key_Escape), self)
        limpiar.activated.connect(self._limpiar_filtros)

    def _enfocar_buscador(self) -> None:
        self.buscador.setFocus()
        self.buscador.selectAll()

    def enfocar_fuente(self, fuente_id: str) -> None:
        card = next(
            (c for g in self._grids for c in g.widgets() if c.fuente.id == fuente_id),
            None,
        )
        if card is None:
            return

        self._filtro_estado = "todas"
        self.buscador.setText(card.fuente.label)
        self._busqueda = card.fuente.label.strip().lower()
        self._aplicar_filtros()
        QTimer.singleShot(
            0, lambda: self._scroll.ensureWidgetVisible(card, 0, 24)
        )

    def _limpiar_filtros(self) -> None:
        self.buscador.clear()
        self._busqueda = ""
        self._filtro_estado = "todas"
        self._aplicar_filtros()


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
            "Muestra u oculta el panel lateral que verifica qué archivos "
            "existen realmente en disco."
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
        layout.addWidget(self._construir_filtros())

        self.progreso = QProgressBar()
        self.progreso.setRange(0, 0)
        self.progreso.setTextVisible(False)
        self.progreso.setFixedHeight(4)
        self.progreso.hide()
        layout.addWidget(self.progreso)

        self.lbl_en_curso = QLabel()
        self.lbl_en_curso.setObjectName("CardMeta")
        self.lbl_en_curso.hide()
        layout.addWidget(self.lbl_en_curso)

        if self.hallazgo.descripcion:
            desc = QLabel(self.hallazgo.descripcion)
            desc.setObjectName("Breadcrumb")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        return barra

    def _construir_filtros(self) -> QWidget:
        barra = ContenedorFlow(espacio_h=8, espacio_v=8)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar fuente…")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.setFixedWidth(230)
        self.buscador.setToolTip(
            "Filtra por nombre de fuente o de archivo. Atajo: Ctrl+F"
        )
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(180)
        self._debounce.timeout.connect(self._al_buscar)
        self.buscador.textChanged.connect(lambda _: self._debounce.start())
        barra.agregar(self.buscador)

        self.chips: dict[str, QPushButton] = {}
        for clave, etiqueta in FILTROS:
            chip = QPushButton(etiqueta)
            chip.setProperty("variante", "chip")
            chip.setProperty("activo", "si" if clave == "todas" else "")
            if clave == "error":
                chip.setProperty("tono", "error")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda _=False, c=clave: self._filtrar_por(c))
            barra.agregar(chip)
            self.chips[clave] = chip

        return barra

    def _al_cambiar_ocupacion(self, ocupado: bool) -> None:
        self._en_curso = max(0, self._en_curso + (1 if ocupado else -1))

        activo = self._en_curso > 0
        self.progreso.setVisible(activo)
        self.lbl_en_curso.setVisible(activo)
        if activo:
            plural = "archivos" if self._en_curso != 1 else "archivo"
            self.lbl_en_curso.setText(
                f"Procesando {self._en_curso} {plural}…"
            )

    def _al_buscar(self) -> None:
        self._busqueda = self.buscador.text().strip().lower()
        self._aplicar_filtros()

    def _filtrar_por(self, clave: str) -> None:
        if self._filtro_estado == clave and clave != "todas":
            clave = "todas"
        self._filtro_estado = clave
        self._aplicar_filtros()

    def _coincide(self, card) -> bool:
        if self._busqueda and self._busqueda not in card.texto_busqueda():
            return False
        if self._filtro_estado == "todas":
            return True
        return card.estado_actual() == self._filtro_estado

    def _aplicar_filtros(self) -> None:
        visibles_total = 0

        for titulo, grid in self._secciones:
            cards = grid.widgets()
            visibles = 0
            for card in cards:
                mostrar = self._coincide(card)
                card.setVisible(mostrar)
                visibles += int(mostrar)

            titulo.setVisible(visibles > 0)
            grid.setVisible(visibles > 0)
            if visibles:
                grupo = titulo.property("grupo")
                titulo.setText(
                    f"{grupo.upper()}  ·  {visibles}"
                    if visibles == len(cards)
                    else f"{grupo.upper()}  ·  {visibles} de {len(cards)}"
                )
                grid.recolocar()
            visibles_total += visibles

        self.sin_resultados.setVisible(visibles_total == 0)
        self._actualizar_chips()

    def _actualizar_chips(self) -> None:
        conteo = {clave: 0 for clave, _ in FILTROS}
        total = 0
        for _, grid in self._secciones:
            for card in grid.widgets():
                total += 1
                estado = card.estado_actual()
                if estado in conteo:
                    conteo[estado] += 1
        conteo["todas"] = total

        for clave, etiqueta in FILTROS:
            chip = self.chips[clave]
            cantidad = conteo[clave]
            chip.setText(f"{etiqueta} ({cantidad})")
            chip.setEnabled(cantidad > 0 or clave == "todas")
            chip.setProperty("activo", "si" if clave == self._filtro_estado else "")
            chip.style().unpolish(chip)
            chip.style().polish(chip)


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
            titulo.setProperty("grupo", grupo)
            self._cuerpo.addWidget(titulo)

            grid = GridResponsivo(
                ancho_min=ANCHO_MIN_CARD,
                espacio=16,
                max_columnas=MAX_COLUMNAS_CARD,
                ancho_max=ANCHO_MAX_CARD,
            )
            for fuente in fuentes:
                card = FuenteCard(fuente)
                card.cambiado.connect(self.refrescar)
                card.ver_datos.connect(self._abrir_datos)
                card.ocupado_cambiado.connect(self._al_cambiar_ocupacion)
                grid.agregar(card)
                self.cards.append(card)

            self._grids.append(grid)
            self._secciones.append((titulo, grid))
            self._cuerpo.addWidget(grid)


    def refrescar(self) -> None:
        for card in self.cards:
            card.refrescar()
        if hasattr(self, "panel") and self.panel.isVisible():
            self.panel.refrescar()

        slots = [s for f in self.hallazgo.fuentes for s in f.slots]
        cargados = sum(1 for s in slots if estado_slot(s).existe)
        total = len(slots)
        obligatorios = self.hallazgo.slots_requeridos
        faltan = sum(1 for s in obligatorios if not estado_slot(s).existe)
        completo = faltan == 0 and len(obligatorios) > 0

        self.lbl_progreso.setText(f"{cargados} / {total} archivos cargados")
        self.lbl_progreso.setProperty("tono", "ok" if completo else "pendiente")
        self.lbl_progreso.style().unpolish(self.lbl_progreso)
        self.lbl_progreso.style().polish(self.lbl_progreso)

        self.btn_generar.setEnabled(completo)
        if completo:
            self.btn_generar.setText("Generar Hallazgos  →")
            pendientes = total - cargados
            self.btn_generar.setToolTip(
                "Las fuentes obligatorias están cargadas. Ir a la pantalla de "
                "hallazgos." + (
                    f" Quedan {pendientes} fuentes opcionales sin cargar; "
                    "no son necesarias." if pendientes else ""
                )
            )
        else:
            plural = "archivos" if faltan != 1 else "archivo"
            self.btn_generar.setText(f"Faltan {faltan} {plural} obligatorio(s)")
            self.btn_generar.setToolTip(
                f"Carga los {faltan} {plural} obligatorio(s) que faltan para "
                "poder generar."
            )

        if self._secciones:
            self._aplicar_filtros()

        self.progreso_cambiado.emit(self.hallazgo.id, cargados, total)


    def _aplicar_panel(self, visible: bool) -> None:
        self.panel.setVisible(visible)
        self.btn_panel.setText(
            "Ocultar estado de archivos" if visible else "Ver estado de archivos"
        )
        if visible:
            self.panel.refrescar()

    def _alternar_panel(self) -> None:
        self._panel_forzado = not self.panel.isVisible()
        preferencias.guardar_panel(self._panel_forzado)
        self._aplicar_panel(self._panel_forzado)

    def _ocultar_panel(self) -> None:
        self._panel_forzado = False
        preferencias.guardar_panel(False)
        self._aplicar_panel(False)

    def _panel_automatico(self) -> None:
        sobre = self.width() >= UMBRAL_PANEL

        if sobre != self._sobre_umbral:
            self._sobre_umbral = sobre
            self._panel_forzado = None
            preferencias.guardar_panel(None)

        if self._panel_forzado is None:
            self._aplicar_panel(sobre)

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._panel_automatico()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._panel_automatico()


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
            f"«Este hallazgo» elimina los archivos cargados de {self.hallazgo.label}.\n\n"
            f"«Toda la certificación» elimina los archivos cargados de TODOS los "
            f"hallazgos de {self.hallazgo.cert_label}.\n\n"
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
