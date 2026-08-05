from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDateEdit, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QTableView, QVBoxLayout, QWidget,
)

from app.cache import store
from app.cache.store import EstadoCache
from app.catalog import formatos, hallazgo_columns as cols, resumenes
from app.catalog.hallazgos import Hallazgo
from app.exports import excel
from app.generation import reports
from app.storage.files import estado_slot
from app.tasks.runner import POOL, Tarea
from app.ui import theme
from app.ui.responsive import ContenedorFlow
from app.ui.table_header import CabeceraColoreada
from app.ui.table_model import DataFrameModel

BANDERAS_KPI = [
    "is_cesado_activo", "is_login_post_cese", "is_no_identificado",
    "is_sin_uso_90d", "is_deshabilitado_180d", "is_no_cesado_oportunamente",
]

#: Debajo de este ancho la fecha de corte y el buscador pasan a una fila propia.
UMBRAL_COMPACTO = 1000


class HallazgoView(QWidget):
    ir_cargar = Signal(str)
    cambiado = Signal()

    def __init__(self, hallazgo: Hallazgo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hallazgo = hallazgo
        self._generando = False
        self._segundos = 0
        self.setObjectName("Canvas")

        self._reloj = QTimer(self)
        self._reloj.setInterval(1000)
        self._reloj.timeout.connect(self._tic)

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

        # Tarjetas de conteo: bajan de línea solas en ventanas angostas.
        self.kpis = ContenedorFlow(espacio_h=12, espacio_v=12)
        self.kpis.hide()
        layout.addWidget(self.kpis)

        self.vacio = self._construir_vacio()
        layout.addWidget(self.vacio, 1)

        self.modelo = DataFrameModel()
        self.tabla = QTableView()
        self.tabla.setModel(self.modelo)
        self.tabla.setSelectionBehavior(QTableView.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(30)

        self.tabla.setHorizontalHeader(CabeceraColoreada(self.tabla))
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.hide()
        layout.addWidget(self.tabla, 1)

        raiz.addWidget(cuerpo, 1)
        self.refrescar()

    # ------------------------------------------------------------------
    # Cabecera
    # ------------------------------------------------------------------

    def _cabecera(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("TopBar")
        layout = QVBoxLayout(barra)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(8)

        breadcrumb = QLabel(
            f"{self.hallazgo.cert_label}  ›  {self.hallazgo.label}  ›  Hallazgos"
        )
        breadcrumb.setObjectName("Breadcrumb")
        breadcrumb.setWordWrap(True)
        layout.addWidget(breadcrumb)

        titulo_fila = QHBoxLayout()
        titulo_fila.setSpacing(10)

        titulo = QLabel(self.hallazgo.label)
        titulo.setObjectName("Titulo")
        titulo_fila.addWidget(titulo)

        self.estado_badge = QLabel()
        self.estado_badge.setObjectName("Badge")
        titulo_fila.addWidget(self.estado_badge)

        self.lbl_filas = QLabel()
        self.lbl_filas.setObjectName("CardMeta")
        titulo_fila.addWidget(self.lbl_filas)
        titulo_fila.addStretch(1)
        layout.addLayout(titulo_fila)

        acciones = ContenedorFlow(espacio_h=8, espacio_v=8)

        self.fecha: QDateEdit | None = None
        if self.hallazgo.usa_fecha_corte:
            caja_fecha = QWidget()
            caja_fecha.setObjectName("Canvas")
            fila_fecha = QHBoxLayout(caja_fecha)
            fila_fecha.setContentsMargins(0, 0, 0, 0)
            fila_fecha.setSpacing(6)

            etiqueta_fecha = QLabel("Fecha de corte")
            etiqueta_fecha.setObjectName("CardMeta")
            fila_fecha.addWidget(etiqueta_fecha)

            self.fecha = QDateEdit()
            theme.configurar_fecha(self.fecha)
            self.fecha.setToolTip(
                "Fecha de referencia para los cálculos de días sin uso y cese oportuno."
            )
            fila_fecha.addWidget(self.fecha)

            btn_hoy = QPushButton("Hoy")
            btn_hoy.setProperty("variante", "ghost")
            btn_hoy.setCursor(Qt.PointingHandCursor)
            btn_hoy.setToolTip("Usar la fecha actual")
            btn_hoy.clicked.connect(
                lambda: self.fecha and self.fecha.setDate(QDate.currentDate())
            )
            fila_fecha.addWidget(btn_hoy)

            acciones.agregar(caja_fecha)

        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("Buscar en los hallazgos…")
        self.buscador.setClearButtonEnabled(True)
        self.buscador.setMinimumWidth(200)
        self.buscador.setMaximumWidth(280)
        self.buscador.textChanged.connect(self._filtrar)
        acciones.agregar(self.buscador)

        self.btn_cargar = QPushButton("Cargar Información")
        self.btn_cargar.setProperty("variante", "ghost")
        self.btn_cargar.setCursor(Qt.PointingHandCursor)
        self.btn_cargar.setToolTip("Ir a la pantalla de carga de archivos fuente.")
        self.btn_cargar.clicked.connect(lambda: self.ir_cargar.emit(self.hallazgo.id))
        acciones.agregar(self.btn_cargar)

        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setProperty("variante", "ghost")
        self.btn_exportar.setCursor(Qt.PointingHandCursor)
        self.btn_exportar.clicked.connect(self._exportar)
        acciones.agregar(self.btn_exportar)

        self.btn_generar = QPushButton("Generar Hallazgos")
        self.btn_generar.setCursor(Qt.PointingHandCursor)
        self.btn_generar.clicked.connect(self._generar)
        acciones.agregar(self.btn_generar)

        layout.addWidget(acciones)
        return barra

    def _construir_vacio(self) -> QWidget:
        marco = QFrame()
        marco.setObjectName("EstadoVacio")
        layout = QVBoxLayout(marco)
        layout.setContentsMargins(32, 48, 32, 48)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        self.vacio_titulo = QLabel("Aún no has generado los hallazgos.")
        self.vacio_titulo.setObjectName("EstadoVacioTitulo")
        self.vacio_titulo.setAlignment(Qt.AlignCenter)
        self.vacio_titulo.setWordWrap(True)
        layout.addWidget(self.vacio_titulo)

        self.vacio_detalle = QLabel()
        self.vacio_detalle.setObjectName("EstadoVacioDetalle")
        self.vacio_detalle.setAlignment(Qt.AlignCenter)
        self.vacio_detalle.setWordWrap(True)
        self.vacio_detalle.setMaximumWidth(560)
        layout.addWidget(self.vacio_detalle, 0, Qt.AlignHCenter)

        self.vacio_boton = QPushButton("Generar Hallazgos")
        self.vacio_boton.setCursor(Qt.PointingHandCursor)
        # Mismo destino que el botón de la barra superior: sin esta conexión el
        # botón del estado vacío quedaba decorativo.
        self.vacio_boton.clicked.connect(self._generar)
        layout.addWidget(self.vacio_boton, 0, Qt.AlignHCenter)

        return marco

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    def refrescar(self) -> None:
        if self._generando:
            return

        slots = [s for f in self.hallazgo.fuentes for s in f.slots]
        faltantes = [s for s in slots if not estado_slot(s).existe]
        conectado = reports.disponible(self.hallazgo.id)
        hay_datos = self.modelo.total_original > 0

        estado = store.estado(self.hallazgo) if conectado else EstadoCache.AUSENTE
        meta = store.leer_meta(self.hallazgo)

        if conectado and estado is not EstadoCache.AUSENTE and not hay_datos:
            self._cargar_cache()
            hay_datos = self.modelo.total_original > 0

        puede_generar = conectado and not faltantes
        self.btn_generar.setEnabled(puede_generar)
        self.vacio_boton.setEnabled(puede_generar)

        if not conectado:
            texto_boton = "No disponible"
            tip = "Este hallazgo aún no está conectado a su reporte en logic/."
        elif faltantes:
            plural = "archivos" if len(faltantes) != 1 else "archivo"
            texto_boton = f"Faltan {len(faltantes)} {plural}"
            tip = f"Carga los {len(faltantes)} {plural} que faltan para poder generar."
        elif hay_datos:
            texto_boton = "Regenerar Hallazgos"
            tip = "Vuelve a ejecutar el reporte con las fuentes actuales."
        else:
            texto_boton = "Generar Hallazgos"
            tip = "Ejecuta el reporte. Puede tardar varios minutos."

        self.btn_generar.setText(texto_boton)
        self.btn_generar.setToolTip(tip)
        self.vacio_boton.setText(
            "Generar Hallazgos" if puede_generar else texto_boton
        )
        self.vacio_boton.setToolTip(tip)

        if not conectado:
            self._badge("NO DISPONIBLE", "pendiente")
            self._vacio(
                "Este hallazgo todavía no está conectado.",
                "La generación aún no está enlazada a su reporte en logic/. "
                "Puedes cargar los archivos fuente mientras tanto.",
            )
        elif faltantes and not hay_datos:
            self._badge("FALTAN FUENTES", "aviso")
            nombres = ", ".join(s.display_label for s in faltantes[:4])
            if len(faltantes) > 4:
                nombres += f" y {len(faltantes) - 4} más"
            self._vacio(
                f"Faltan {len(faltantes)} de {len(slots)} archivos por cargar.",
                f"Pendientes: {nombres}. Usa «Cargar Información» para completarlos.",
            )
        elif faltantes:
            self._badge("FALTAN FUENTES", "aviso")
            self._mostrar_aviso(
                f"Faltan {len(faltantes)} de {len(slots)} archivos. Los datos "
                "mostrados corresponden a la última generación completa.", "aviso")
        elif estado is EstadoCache.DESACTUALIZADA:
            self._badge("DESACTUALIZADO", "aviso")
            self._mostrar_aviso(
                "Las fuentes cambiaron desde la última generación. "
                "Los datos mostrados corresponden a la ejecución anterior.", "aviso")
        elif estado is EstadoCache.VIGENTE and meta:
            self._badge("VIGENTE", "ok")
            self.aviso.hide()
        else:
            self._badge("SIN GENERAR", "pendiente")
            self.aviso.hide()
            self._vacio(
                "Aún no has generado los hallazgos.",
                "El reporte solo se ejecuta cuando lo pides."
                + (
                    " Elige la fecha de corte y presiona «Generar Hallazgos»."
                    if self.hallazgo.usa_fecha_corte
                    else " Presiona «Generar Hallazgos» para empezar."
                ),
            )

        self._alternar_contenido(hay_datos)

        if hay_datos and meta:
            self.lbl_filas.setText(
                f"{self.modelo.total_original:,} filas · generado {meta.generado_texto}"
                .replace(",", " ")
            )
        else:
            self.lbl_filas.setText("")

        self.btn_exportar.setEnabled(hay_datos)
        self.buscador.setEnabled(hay_datos)

    def _alternar_contenido(self, hay_datos: bool) -> None:
        self.tabla.setVisible(hay_datos)
        self.kpis.setVisible(hay_datos)
        self.vacio.setVisible(not hay_datos and not self._generando)

    def _vacio(self, titulo: str, detalle: str) -> None:
        self.vacio_titulo.setText(titulo)
        self.vacio_detalle.setText(detalle)

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

    # ------------------------------------------------------------------
    # Generación
    # ------------------------------------------------------------------

    def _tic(self) -> None:
        self._segundos += 1
        minutos, segundos = divmod(self._segundos, 60)
        etiqueta = f"Generando…  {minutos:02d}:{segundos:02d}"
        self.btn_generar.setText(etiqueta)
        self.vacio_boton.setText(etiqueta)

    def _generar(self) -> None:
        self._generando = True
        self._segundos = 0
        self.btn_generar.setEnabled(False)
        self.vacio_boton.setEnabled(False)
        self.btn_exportar.setEnabled(False)
        self.barra.show()
        self._reloj.start()
        self._tic()
        self._badge("GENERANDO…", "aviso")
        self._mostrar_aviso(
            "Procesando las fuentes. Esto puede tardar varios minutos según el "
            "volumen de datos.", "aviso")

        fecha_ref: date = (
            self.fecha.date().toPython() if self.fecha is not None else date.today()
        )
        tarea = Tarea(reports.generar, self.hallazgo.id, fecha_ref)
        tarea.senales.ok.connect(self._al_generar)
        tarea.senales.error.connect(self._al_fallar)
        POOL.start(tarea)

    def _al_generar(self, df) -> None:
        self._generando = False
        self._reloj.stop()
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
        self._reloj.stop()
        self.barra.hide()
        self._badge("ERROR", "error")
        self._mostrar_aviso(f"No se pudo generar el hallazgo: {mensaje}", "error")
        self.btn_generar.setEnabled(True)
        self.btn_generar.setText("Reintentar")
        self.vacio_boton.setEnabled(True)
        self.vacio_boton.setText("Reintentar")
        self._alternar_contenido(self.modelo.total_original > 0)

    def _cargar_cache(self) -> None:
        resultado = store.cargar(self.hallazgo)
        if resultado.df is not None:
            self._pintar(resultado.df)

    def _pintar(self, df) -> None:
        self.modelo.set_dataframe(df, self.hallazgo.modelo)
        self.buscador.clear()
        self._construir_kpis(df)
        # El ancho lo manda `hallazgo_columns.py`, no el contenido: así la
        # tabla se ve igual con 10 filas que con 90 000.
        for col in range(self.modelo.columnCount()):
            campo = str(self.modelo.dataframe.columns[col])
            self.tabla.setColumnWidth(col, cols.ancho(self.hallazgo.modelo, campo))
        self.btn_exportar.setEnabled(len(df) > 0)

    def _construir_kpis(self, df) -> None:
        while self.kpis.flow.count():
            item = self.kpis.flow.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        etiquetas = cols.etiquetas(self.hallazgo.modelo)
        tarjetas = [("Total de filas", len(df))]
        for campo in BANDERAS_KPI:
            if campo in df.columns:
                # Conteo tolerante: cuenta True y también "X" si el DataFrame
                # llegara ya como texto desde una caché antigua.
                conteo = formatos.contar_verdaderos(df[campo])
                tarjetas.append((etiquetas.get(campo, campo), conteo))

        for etiqueta, valor in tarjetas:
            tarjeta = QFrame()
            tarjeta.setObjectName("KpiCard")
            tarjeta.setMinimumWidth(150)
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

            self.kpis.agregar(tarjeta)

        self.kpis.setVisible(bool(tarjetas))

    # ------------------------------------------------------------------
    # Filtro y exportación
    # ------------------------------------------------------------------

    def _filtrar(self, texto: str) -> None:
        self.modelo.aplicar_filtro(texto)
        total = self.modelo.total_original
        visibles = len(self.modelo.dataframe)
        if texto.strip() and total:
            self.lbl_filas.setText(
                f"{visibles:,} de {total:,} filas".replace(",", " ")
            )
        elif total:
            meta = store.leer_meta(self.hallazgo)
            sufijo = f" · generado {meta.generado_texto}" if meta else ""
            self.lbl_filas.setText(f"{total:,} filas".replace(",", " ") + sufijo)

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

        tarea = Tarea(
            excel.exportar, df, destino, self.hallazgo.modelo, "Hallazgos",
            resumenes.COLUMNAS_EDITABLES
            if resumenes.disponible(self.hallazgo.id) else (),
        )
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
