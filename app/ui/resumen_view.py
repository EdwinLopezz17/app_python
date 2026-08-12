from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QMessageBox,
    QProgressBar, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from app.catalog import resumenes
from app.catalog.hallazgos import Hallazgo
from app.resumen import engine, export
from app.resumen.importer import ErrorDeImportacion, leer_detalle
from app.tasks.runner import POOL, Tarea
from app.ui.responsive import ContenedorFlow

FILTRO_ARCHIVOS = "Excel de detalle (*.xlsx *.xlsm *.xls);;Todos los archivos (*)"
EXTENSIONES = {".xlsx", ".xlsm", ".xls"}


def _tamano_texto(bytes_: int) -> str:
    valor = float(bytes_)
    for unidad in ("B", "KB", "MB", "GB"):
        if valor < 1024 or unidad == "GB":
            return f"{valor:.1f} {unidad}" if unidad != "B" else f"{int(valor)} B"
        valor /= 1024
    return f"{valor:.1f} GB"


class ZonaSoltar(QFrame):
    archivo = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ZonaSoltar")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        self.titulo = QLabel("Arrastra el Excel aquí o haz clic para seleccionarlo")
        self.titulo.setObjectName("ZonaSoltarTitulo")
        self.titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.titulo)

        self.detalle = QLabel("Formato .xlsx")
        self.detalle.setObjectName("CardMeta")
        self.detalle.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detalle)

    def _valido(self, evento) -> str | None:
        if not evento.mimeData().hasUrls():
            return None
        for url in evento.mimeData().urls():
            ruta = url.toLocalFile()
            if url.isLocalFile() and Path(ruta).suffix.lower() in EXTENSIONES:
                return ruta
        return None

    def _marcar(self, activa: bool) -> None:
        self.setProperty("soltar", "activa" if activa else "")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, evento) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Excel de detalle", "", FILTRO_ARCHIVOS
        )
        if ruta:
            self.archivo.emit(ruta)

    def dragEnterEvent(self, evento: QDragEnterEvent) -> None:
        if self._valido(evento):
            evento.acceptProposedAction()
            self._marcar(True)
        else:
            evento.ignore()

    def dragMoveEvent(self, evento) -> None:
        evento.acceptProposedAction() if self._valido(evento) else evento.ignore()

    def dragLeaveEvent(self, evento) -> None:
        self._marcar(False)
        evento.accept()

    def dropEvent(self, evento: QDropEvent) -> None:
        self._marcar(False)
        ruta = self._valido(evento)
        if not ruta:
            evento.ignore()
            return
        evento.acceptProposedAction()
        self.archivo.emit(ruta)


class ResumenView(QWidget):
    ir_hallazgo = Signal(str)

    def __init__(self, hallazgo: Hallazgo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hallazgo = hallazgo
        self.config = resumenes.get(hallazgo.id)
        self._filas: list[dict] = []
        self._archivo = ""

        self.setObjectName("Canvas")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)
        raiz.addWidget(self._cabecera())

        cuerpo = QWidget()
        cuerpo.setObjectName("Canvas")
        layout = QVBoxLayout(cuerpo)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(14)

        layout.addWidget(self._instrucciones())

        self.zona = ZonaSoltar()
        self.zona.archivo.connect(self._procesar)
        layout.addWidget(self.zona)

        self.barra = QProgressBar()
        self.barra.setRange(0, 0)
        self.barra.hide()
        layout.addWidget(self.barra)

        self.aviso = QLabel()
        self.aviso.setObjectName("Badge")
        self.aviso.setWordWrap(True)
        self.aviso.hide()
        layout.addWidget(self.aviso)

        self.kpis = ContenedorFlow(espacio_h=12, espacio_v=12)
        self._kpis_layout = self.kpis.flow
        self.kpis.hide()
        layout.addWidget(self.kpis)

        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        cabecera_tabla = self.tabla.horizontalHeader()
        cabecera_tabla.setSectionResizeMode(QHeaderView.Interactive)
        # Sin estirar la última columna: las columnas numéricas (N°, GDH, ACC)
        # son de 2-3 dígitos y no tienen por qué llegar al borde de la ventana.
        # El espacio que sobre se le da a la primera columna, que es la de
        # texto largo (escenario de monitoreo / título del escenario).
        cabecera_tabla.setStretchLastSection(False)
        cabecera_tabla.setMinimumSectionSize(56)
        # Si el usuario arrastra una columna, dejamos de recalcular anchos:
        # su ajuste manda hasta que se cargue otro archivo.
        self._anchos_manuales = False
        self._ajustando = False
        cabecera_tabla.sectionResized.connect(self._al_mover_columna)
        self.tabla.hide()
        layout.addWidget(self.tabla, 1)

        raiz.addWidget(cuerpo, 1)


    def _cabecera(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("TopBar")
        layout = QVBoxLayout(barra)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(6)

        breadcrumb = QLabel(
            f"{self.hallazgo.cert_label}  ›  Hallazgos  ›  {self.hallazgo.label}"
            "  ›  Generar Resumen"
        )
        breadcrumb.setObjectName("Breadcrumb")
        breadcrumb.setWordWrap(True)
        layout.addWidget(breadcrumb)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        titulo = QLabel("Generar Resumen")
        titulo.setObjectName("Titulo")
        fila.addWidget(titulo)
        fila.addStretch(1)
        layout.addLayout(fila)

        acciones = ContenedorFlow(espacio_h=8, espacio_v=8)

        self.btn_otro = QPushButton("Procesar otro archivo")
        self.btn_otro.setProperty("variante", "ghost")
        self.btn_otro.setCursor(Qt.PointingHandCursor)
        self.btn_otro.setToolTip("Volver a la zona de carga para subir otro Excel.")
        self.btn_otro.clicked.connect(self.reiniciar)
        self.btn_otro.setEnabled(False)
        acciones.agregar(self.btn_otro)

        self.btn_descargar = QPushButton("Descargar Resumen")
        self.btn_descargar.setCursor(Qt.PointingHandCursor)
        self.btn_descargar.setToolTip(
            "Genera el .xlsx con una hoja por escenario y el consolidado."
        )
        self.btn_descargar.clicked.connect(self._descargar)
        self.btn_descargar.setEnabled(False)
        acciones.agregar(self.btn_descargar)

        layout.addWidget(acciones)
        return barra

    def _instrucciones(self) -> QWidget:
        tarjeta = QFrame()
        tarjeta.setObjectName("Card")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        titulo = QLabel("¿Cómo funciona?")
        titulo.setObjectName("CardTitulo")
        layout.addWidget(titulo)

        pasos = [
            f"1.  En «{self.hallazgo.label}» exporta el Excel de detalle.",
            "2.  Llena la columna Responsable con GDH, ACCESOS o «GDH | ACCESOS» "
            "(y Comentario si aplica) y guarda.",
            "3.  Sube aquí ese mismo archivo y descarga el resumen por escenarios "
            f"({self.config.escenarios[0].code} a {self.config.escenarios[-1].code}).",
        ]
        for texto in pasos:
            paso = QLabel(texto)
            paso.setObjectName("CardMeta")
            paso.setWordWrap(True)
            layout.addWidget(paso)

        return tarjeta


    def _procesar(self, ruta: str) -> None:
        self._archivo = Path(ruta).name
        self.aviso.hide()
        self.barra.show()
        self.zona.setEnabled(False)

        tarea = Tarea(leer_detalle, ruta, self.config.modelo)
        tarea.senales.ok.connect(self._al_leer)
        tarea.senales.error.connect(self._al_fallar)
        POOL.start(tarea)

    def _al_leer(self, filas) -> None:
        self.barra.hide()
        self.zona.setEnabled(True)

        if not filas:
            self._al_fallar("No se encontraron filas de datos en el archivo.")
            return

        self._filas = list(filas)
        self.zona.hide()
        self.btn_otro.setEnabled(True)
        self.btn_descargar.setEnabled(True)
        self._mostrar_aviso(
            f"Resumen listo · {self._archivo} · {len(self._filas)} filas leídas", "ok"
        )
        self._pintar_preview()

    def _al_fallar(self, mensaje: str) -> None:
        self.barra.hide()
        self.zona.setEnabled(True)
        self._filas = []
        self.tabla.hide()
        self.kpis.hide()
        self.btn_descargar.setEnabled(False)
        self._mostrar_aviso(f"No se pudo procesar el archivo: {mensaje}", "error")

    def reiniciar(self) -> None:
        self._filas = []
        self._archivo = ""
        self.tabla.hide()
        self.kpis.hide()
        self.aviso.hide()
        self.zona.show()
        self.btn_otro.setEnabled(False)
        self.btn_descargar.setEnabled(False)

    def _mostrar_aviso(self, texto: str, tono: str) -> None:
        self.aviso.setText(texto)
        self.aviso.setProperty("tono", tono)
        self.aviso.style().unpolish(self.aviso)
        self.aviso.style().polish(self.aviso)
        self.aviso.show()


    def _pintar_preview(self) -> None:
        if self.config.campo_grupo:
            self._preview_por_grupo()
        else:
            self._preview_por_escenario()
        self.tabla.show()
        self._anchos_manuales = False
        self._ajustar_anchos(forzar=True)

    ANCHO_MAX_COLUMNA = 420
    RELLENO_COLUMNA = 24

    def _al_mover_columna(self, *_: int) -> None:
        if not self._ajustando:
            self._anchos_manuales = True

    def _ajustar_anchos(self, forzar: bool = False) -> None:
        """Ancho por contenido, con el sobrante para la primera columna."""
        tabla = self.tabla
        if tabla.columnCount() == 0:
            return
        if self._anchos_manuales and not forzar:
            return

        self._ajustando = True
        try:
            tabla.resizeColumnsToContents()

            for col in range(tabla.columnCount()):
                ancho = tabla.columnWidth(col) + self.RELLENO_COLUMNA
                tabla.setColumnWidth(col, min(ancho, self.ANCHO_MAX_COLUMNA))

            disponible = tabla.viewport().width()
            usado = sum(tabla.columnWidth(c) for c in range(tabla.columnCount()))
            sobra = disponible - usado
            if sobra > 0:
                tabla.setColumnWidth(0, tabla.columnWidth(0) + sobra)
        finally:
            self._ajustando = False

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        if self.tabla.isVisible() and self.tabla.columnCount():
            self._ajustar_anchos()

    def _preview_por_escenario(self) -> None:
        resumen = engine.por_escenario(self._filas, self.config.escenarios)
        self._pintar_kpis([
            ("Registros leídos", resumen.total_registros),
            ("Escenarios con datos", resumen.escenarios_con_datos),
            ("Total hallazgos", resumen.total_hallazgos),
        ])

        cabeceras = ["Hoja", "Escenario", "N°", "GDH", "ACCESOS"]
        self.tabla.setColumnCount(len(cabeceras))
        self.tabla.setHorizontalHeaderLabels(cabeceras)
        self.tabla.setRowCount(len(resumen.filas) + 1)

        for indice, fila in enumerate(resumen.filas):
            self._celda(indice, 0, fila.code)
            self._celda(indice, 1, fila.title)
            self._celda(indice, 2, fila.total, numero=True)
            self._celda(indice, 3, fila.gdh, numero=True)
            self._celda(indice, 4, fila.accesos, numero=True)

        ultima = len(resumen.filas)
        self._celda(ultima, 0, "TOTAL", negrita=True)
        self._celda(ultima, 1, "", negrita=True)
        self._celda(ultima, 2, resumen.total_hallazgos, numero=True, negrita=True)
        self._celda(ultima, 3, resumen.total_gdh, numero=True, negrita=True)
        self._celda(ultima, 4, resumen.total_accesos, numero=True, negrita=True)

    def _preview_por_grupo(self) -> None:
        escenarios = list(self.config.escenarios)
        resumen = engine.por_grupo(self._filas, escenarios, self.config.campo_grupo or "")

        self._pintar_kpis(
            [(self.config.etiqueta_grupo or "Grupos", len(resumen.filas))]
            + [(e.code, resumen.total.total(e.code)) for e in escenarios]
            + [("Total hallazgos", resumen.total_hallazgos)]
        )

        cabeceras = [self.config.etiqueta_grupo or "Grupo"]
        posiciones: list[int] = []
        for indice, escenario in enumerate(escenarios, start=1):
            posiciones.append(len(cabeceras))
            cabeceras.append(f"H{indice} N°")
            if escenario.reporta_responsable:
                cabeceras += [f"H{indice} GDH", f"H{indice} ACC"]
        self.tabla.setColumnCount(len(cabeceras))
        self.tabla.setHorizontalHeaderLabels(cabeceras)
        self.tabla.setRowCount(len(resumen.filas) + 1)

        def escribir(indice: int, fila: engine.FilaGrupo, negrita: bool) -> None:
            self._celda(indice, 0, fila.grupo, negrita=negrita)
            for pos, escenario in enumerate(escenarios):
                base = posiciones[pos]
                self._celda(indice, base, fila.total(escenario.code), True, negrita)
                if escenario.reporta_responsable:
                    self._celda(indice, base + 1, fila.gdh(escenario.code), True, negrita)
                    self._celda(indice, base + 2, fila.accesos(escenario.code), True, negrita)

        for indice, fila in enumerate(resumen.filas):
            escribir(indice, fila, False)
        escribir(len(resumen.filas), resumen.total, True)

    def _celda(self, fila: int, col: int, valor, numero: bool = False,
               negrita: bool = False) -> None:
        item = QTableWidgetItem(str(valor))
        if numero:
            item.setTextAlignment(int(Qt.AlignRight | Qt.AlignVCenter))
        if negrita:
            fuente = item.font()
            fuente.setBold(True)
            item.setFont(fuente)
        self.tabla.setItem(fila, col, item)

    def _pintar_kpis(self, tarjetas: list[tuple[str, int]]) -> None:
        while self._kpis_layout.count():
            elemento = self._kpis_layout.takeAt(0)
            if elemento.widget():
                elemento.widget().deleteLater()

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

            tarjeta.setMinimumWidth(150)
            self._kpis_layout.addWidget(tarjeta)

        self.kpis.show()


    def _descargar(self) -> None:
        if not self._filas:
            return

        destino, _ = QFileDialog.getSaveFileName(
            self, "Guardar resumen", export.nombre_sugerido(self.config),
            "Excel (*.xlsx)",
        )
        if not destino:
            return

        self.btn_descargar.setEnabled(False)
        self.btn_descargar.setText("Generando…")

        tarea = Tarea(export.exportar, self.config, self._filas, destino)
        tarea.senales.ok.connect(self._al_descargar)
        tarea.senales.error.connect(self._al_fallar_descarga)
        # Restauramos el botón en las tres señales: aunque 'terminada' basta,
        # así el botón nunca queda colgado en "Generando…" si una de ellas se
        # pierde. _restaurar_descarga es idempotente.
        tarea.senales.ok.connect(lambda _=None: self._restaurar_descarga())
        tarea.senales.error.connect(lambda _=None: self._restaurar_descarga())
        tarea.senales.terminada.connect(self._restaurar_descarga)
        POOL.start(tarea)

    def _restaurar_descarga(self) -> None:
        if self.btn_descargar.isEnabled():
            return
        self.btn_descargar.setEnabled(True)
        self.btn_descargar.setText("Descargar Resumen")

    def _al_fallar_descarga(self, mensaje: str) -> None:
        self._restaurar_descarga()
        QMessageBox.critical(
            self, "Descargar Resumen", f"No se pudo generar: {mensaje}"
        )

    def _al_descargar(self, ruta) -> None:
        self._restaurar_descarga()

        ruta = Path(ruta)
        # Validamos que el archivo exista de verdad en el disco y no esté
        # vacío: xlsxwriter puede cerrar el libro sin escribir nada si el
        # antivirus corporativo o OneDrive interceptan la escritura.
        try:
            tamano = ruta.stat().st_size
        except OSError:
            tamano = 0

        if tamano <= 0:
            QMessageBox.warning(
                self, "Resumen generado",
                "La generación terminó, pero el archivo no quedó guardado en "
                f"el disco:\n{ruta}\n\nRevisa que la carpeta no esté "
                "sincronizando (OneDrive) y que tengas permisos de escritura.",
            )
            return

        dialogo = QMessageBox(self)
        dialogo.setIcon(QMessageBox.Information)
        dialogo.setWindowTitle("Resumen generado")
        dialogo.setText("El archivo se guardó correctamente.")
        dialogo.setInformativeText(
            f"{ruta}\n\n{_tamano_texto(tamano)} · "
            f"{len(self._filas):,} filas procesadas".replace(",", " ")
        )
        btn_carpeta = dialogo.addButton("Abrir carpeta", QMessageBox.ActionRole)
        dialogo.addButton("Cerrar", QMessageBox.AcceptRole)
        dialogo.exec()

        if dialogo.clickedButton() is btn_carpeta:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(ruta.parent)))
