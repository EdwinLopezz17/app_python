from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app.cache import store
from app.cache.store import EstadoCache
from app.catalog.hallazgos import Certificacion, Hallazgo, certificaciones
from app.generation import reports
from app.storage.files import estado_slot

COLUMNAS = 2


class HallazgoFila(QFrame):

    ir_cargar = Signal(str)
    ir_generar = Signal(str)

    def __init__(self, hallazgo: Hallazgo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hallazgo = hallazgo
        self.setObjectName("CardHallazgo")

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(12, 10, 12, 10)
        raiz.setSpacing(12)

        texto = QVBoxLayout()
        texto.setSpacing(2)
        titulo = QLabel(hallazgo.label)
        titulo.setObjectName("HallazgoTitulo")
        texto.addWidget(titulo)

        self.meta = QLabel()
        self.meta.setObjectName("HallazgoMeta")
        texto.addWidget(self.meta)
        raiz.addLayout(texto, 1)

        self.btn_cargar = QPushButton("Cargar")
        self.btn_cargar.setProperty("variante", "ghost")
        self.btn_cargar.setProperty("clase", "mini")
        self.btn_cargar.setCursor(Qt.PointingHandCursor)
        self.btn_cargar.clicked.connect(lambda: self.ir_cargar.emit(hallazgo.id))
        raiz.addWidget(self.btn_cargar)

        self.btn_generar = QPushButton("Generar")
        self.btn_generar.setCursor(Qt.PointingHandCursor)
        self.btn_generar.clicked.connect(lambda: self.ir_generar.emit(hallazgo.id))
        raiz.addWidget(self.btn_generar)

        self.refrescar()

    def refrescar(self) -> None:
        slots = [s for f in self.hallazgo.fuentes for s in f.slots]
        cargados = sum(1 for s in slots if estado_slot(s).existe)
        total = len(slots)
        completo = cargados == total and total > 0

        partes = [f"{cargados}/{total} archivos"]

        if not reports.disponible(self.hallazgo.id):
            partes.append("generación pendiente")
            self.btn_generar.setEnabled(False)
            self.btn_generar.setToolTip("Este hallazgo aún no está conectado a su reporte.")
        else:
            estado = store.estado(self.hallazgo)
            meta = store.leer_meta(self.hallazgo)
            if estado is EstadoCache.VIGENTE and meta:
                partes.append(f"generado {meta.generado_texto}")
            elif estado is EstadoCache.DESACTUALIZADA:
                partes.append("desactualizado")
            else:
                partes.append("sin generar")

            self.btn_generar.setEnabled(completo)
            self.btn_generar.setToolTip(
                "" if completo else "Faltan archivos por cargar."
            )

        self.meta.setText("  ·  ".join(partes))


class CertificacionCard(QFrame):
    ir_cargar = Signal(str)
    ir_generar = Signal(str)

    def __init__(self, cert: Certificacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.cert = cert
        self.setObjectName("CardCert")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(18, 16, 18, 16)
        raiz.setSpacing(12)

        titulo = QLabel(cert.label)
        titulo.setObjectName("CardCertTitulo")
        titulo.setWordWrap(True)
        raiz.addWidget(titulo)

        subtitulo = QLabel(
            f"{len(cert.hallazgos)} hallazgo(s) · "
            f"{len({fid for h in cert.hallazgos for fid in h.fuente_ids})} fuentes"
        )
        subtitulo.setObjectName("CardCertDesc")
        raiz.addWidget(subtitulo)

        self.filas: list[HallazgoFila] = []
        for hallazgo in cert.hallazgos:
            fila = HallazgoFila(hallazgo)
            fila.ir_cargar.connect(self.ir_cargar.emit)
            fila.ir_generar.connect(self.ir_generar.emit)
            raiz.addWidget(fila)
            self.filas.append(fila)

    def refrescar(self) -> None:
        for fila in self.filas:
            fila.refrescar()


class LauncherView(QWidget):

    ir_cargar = Signal(str)
    ir_generar = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Canvas")

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        raiz.addWidget(self._cabecera())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        contenido.setObjectName("Canvas")
        cuerpo = QVBoxLayout(contenido)
        cuerpo.setContentsMargins(24, 20, 24, 32)
        cuerpo.setSpacing(20)

        cuerpo.addWidget(self._resumen())

        grid_cont = QWidget()
        grid_cont.setObjectName("Canvas")
        grid = QGridLayout(grid_cont)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        self.cards: list[CertificacionCard] = []
        for indice, cert in enumerate(certificaciones()):
            card = CertificacionCard(cert)
            card.ir_cargar.connect(self.ir_cargar.emit)
            card.ir_generar.connect(self.ir_generar.emit)
            grid.addWidget(card, indice // COLUMNAS, indice % COLUMNAS, Qt.AlignTop)
            self.cards.append(card)
        for col in range(COLUMNAS):
            grid.setColumnStretch(col, 1)

        cuerpo.addWidget(grid_cont)
        cuerpo.addStretch(1)
        scroll.setWidget(contenido)
        raiz.addWidget(scroll, 1)

    def _cabecera(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("TopBar")
        layout = QVBoxLayout(barra)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(4)

        breadcrumb = QLabel("Inicio")
        breadcrumb.setObjectName("Breadcrumb")
        layout.addWidget(breadcrumb)

        titulo = QLabel("Certificación de Accesos")
        titulo.setObjectName("Titulo")
        layout.addWidget(titulo)
        return barra

    def _resumen(self) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("Canvas")
        fila = QHBoxLayout(contenedor)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(16)

        self._kpis: dict[str, QLabel] = {}
        for clave, etiqueta in [
            ("archivos", "ARCHIVOS CARGADOS"),
            ("listos", "HALLAZGOS LISTOS PARA GENERAR"),
            ("generados", "HALLAZGOS GENERADOS"),
        ]:
            tarjeta = QFrame()
            tarjeta.setObjectName("KpiCard")
            interno = QVBoxLayout(tarjeta)
            interno.setContentsMargins(18, 14, 18, 14)
            interno.setSpacing(2)

            valor = QLabel("—")
            valor.setObjectName("Kpi")
            interno.addWidget(valor)

            desc = QLabel(etiqueta)
            desc.setObjectName("KpiEtiqueta")
            interno.addWidget(desc)

            self._kpis[clave] = valor
            fila.addWidget(tarjeta, 1)

        return contenedor

    def refrescar(self) -> None:
        for card in self.cards:
            card.refrescar()

        from app.catalog.hallazgos import HALLAZGOS

        slots = {
            s.key: s
            for h in HALLAZGOS for f in h.fuentes for s in f.slots
        }
        cargados = sum(1 for s in slots.values() if estado_slot(s).existe)

        listos = generados = 0
        for hallazgo in HALLAZGOS:
            hs = [s for f in hallazgo.fuentes for s in f.slots]
            if hs and all(estado_slot(s).existe for s in hs):
                listos += 1
            if store.estado(hallazgo) is EstadoCache.VIGENTE:
                generados += 1

        self._kpis["archivos"].setText(f"{cargados} / {len(slots)}")
        self._kpis["listos"].setText(str(listos))
        self._kpis["generados"].setText(str(generados))
