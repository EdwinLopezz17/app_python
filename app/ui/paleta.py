"""Paleta de comandos (Ctrl+K), equivalente a `CommandPalette.tsx`.

Se escribe una palabra y aparecen los destinos como rutas de árbol; Enter o
clic navega. Cubre TODAS las certificaciones, no solo la activa: es la forma
rápida de saltar a «BD Vida» estando en Usuarios sin pasar por el switcher.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPainter
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QSizePolicy, QVBoxLayout, QWidget,
)

from app.ui import theme
from app.ui.search_index import Entrada, buscar

#: Alto de cada resultado. Dos líneas (ruta + hoja) más aire.
ALTO_FILA = 46


class _Fondo(QWidget):
    """Velo oscuro sobre la ventana mientras la paleta está abierta.

    Qt no atenúa lo que hay detrás de un diálogo, así que se pinta un widget
    hijo de la ventana principal, a pantalla completa y por encima de todo.
    Además de centrar la atención, captura los clics: pulsar fuera cierra la
    paleta, como en la referencia web.
    """

    cerrar = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

    def paintEvent(self, evento) -> None:
        pintor = QPainter(self)
        # Alfa 130/255: oscurece lo suficiente para que la paleta domine, sin
        # borrar del todo el contexto de dónde estabas.
        pintor.fillRect(self.rect(), QColor(19, 27, 46, 130))

    def mousePressEvent(self, evento) -> None:
        self.cerrar.emit()

    def mostrar(self) -> None:
        padre = self.parentWidget()
        if padre is not None:
            self.setGeometry(padre.rect())
        self.show()
        self.raise_()


class _Fila(QWidget):
    """Ruta de migas arriba en minúscula, hoja abajo en negrita."""

    def __init__(self, entrada: Entrada, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        columna = QVBoxLayout(self)
        columna.setContentsMargins(12, 5, 12, 5)
        columna.setSpacing(1)

        cola = QLabel("  ›  ".join(entrada.cola))
        cola.setObjectName("PaletaRuta")
        columna.addWidget(cola)

        hoja = QLabel(entrada.hoja)
        hoja.setObjectName("PaletaHoja")
        columna.addWidget(hoja)


class PaletaComandos(QDialog):
    """Diálogo modal sin marco, anclado a la parte alta de la ventana."""

    navegar = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Paleta")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        # No modal a propósito: el velo ya bloquea el resto de la ventana y así
        # puede recibir los clics para cerrar. Con un diálogo modal, Qt se come
        # esos clics y no llegan nunca al velo.
        self.setModal(False)
        self._resultados: list[Entrada] = []

        self.fondo = _Fondo(parent) if parent is not None else None
        if self.fondo is not None:
            self.fondo.cerrar.connect(self.reject)

        marco = QFrame()
        marco.setObjectName("PaletaMarco")
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.addWidget(marco)

        columna = QVBoxLayout(marco)
        columna.setContentsMargins(0, 0, 0, 0)
        columna.setSpacing(0)

        # Sin stretch en ninguno: cabecera y pie con alto fijo, la lista con el
        # alto que se le asigne. Antes la lista llevaba stretch=1 y, al vaciar
        # el texto, el alto sobrante del diálogo se repartía estirando la
        # cabecera y el pie (el recuadro «ESC» crecía hasta ser un rectángulo).
        self._caja_entrada = self._construir_entrada()
        self._caja_pie = self._construir_pie()
        columna.addWidget(self._caja_entrada)
        columna.addWidget(self._construir_lista())
        columna.addWidget(self._caja_pie)

        self.setFixedWidth(620)
        self._refrescar()

    # ------------------------------------------------------------------

    def _construir_entrada(self) -> QWidget:
        caja = QWidget()
        caja.setObjectName("PaletaEntrada")
        caja.setAttribute(Qt.WA_StyledBackground, True)
        caja.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(14, 4, 12, 4)
        fila.setSpacing(10)

        lupa = QLabel("⌕")
        lupa.setObjectName("PaletaLupa")
        fila.addWidget(lupa)

        self.entrada = QLineEdit()
        self.entrada.setObjectName("PaletaInput")
        self.entrada.setPlaceholderText(
            "Buscar hallazgo, pantalla o fuente…   (p. ej. «Active», «GDH»)"
        )
        self.entrada.setFrame(False)
        self.entrada.textChanged.connect(self._refrescar)
        # El QLineEdit se come las flechas para mover el cursor; se interceptan
        # antes para que muevan la selección de la lista.
        self.entrada.installEventFilter(self)
        fila.addWidget(self.entrada, 1)

        esc = QLabel("ESC")
        esc.setObjectName("PaletaTecla")
        fila.addWidget(esc)
        return caja

    def _construir_lista(self) -> QWidget:
        self.lista = QListWidget()
        self.lista.setObjectName("PaletaLista")
        self.lista.setFrameShape(QFrame.NoFrame)
        self.lista.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lista.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.lista.itemActivated.connect(lambda _: self._ir())
        self.lista.itemClicked.connect(lambda _: self._ir())
        return self.lista

    def _construir_pie(self) -> QWidget:
        caja = QWidget()
        caja.setObjectName("PaletaPie")
        caja.setAttribute(Qt.WA_StyledBackground, True)
        caja.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(14, 6, 14, 6)

        ayuda = QLabel("↑ ↓ NAVEGAR  ·  ↵ ABRIR")
        ayuda.setObjectName("PaletaPieTexto")
        fila.addWidget(ayuda)
        fila.addStretch(1)

        self.lbl_conteo = QLabel("·")
        self.lbl_conteo.setObjectName("PaletaPieTexto")
        fila.addWidget(self.lbl_conteo)
        return caja

    # ------------------------------------------------------------------

    def abrir(self) -> None:
        """Limpia, recoloca sobre la ventana padre y enfoca."""
        self.entrada.clear()
        self._refrescar()

        padre = self.parentWidget()
        if padre is not None:
            marco = padre.frameGeometry()
            self.move(
                marco.center().x() - self.width() // 2,
                marco.top() + max(int(marco.height() * 0.12), 40),
            )

        if self.fondo is not None:
            self.fondo.mostrar()

        self.show()
        self.raise_()
        self.activateWindow()
        # Tras el paint: si no, el foco se lo queda el diálogo y no el input.
        QTimer.singleShot(0, self.entrada.setFocus)

    def hideEvent(self, evento) -> None:
        if self.fondo is not None:
            self.fondo.hide()
        super().hideEvent(evento)

    def _refrescar(self) -> None:
        consulta = self.entrada.text().strip()
        self._resultados = buscar(consulta) if consulta else []

        self.lista.clear()
        for entrada in self._resultados:
            item = QListWidgetItem()
            item.setSizeHint(self.lista.sizeHintForIndex(self.lista.rootIndex()))
            item.setSizeHint(_Fila(entrada).sizeHint())
            self.lista.addItem(item)
            self.lista.setItemWidget(item, _Fila(entrada))

        if self._resultados:
            self.lista.setCurrentRow(0)
            self.lbl_conteo.setText(
                f"{len(self._resultados)} RESULTADO"
                f"{'' if len(self._resultados) == 1 else 'S'}"
            )
            self._mensaje(None)
        else:
            self.lbl_conteo.setText("·")
            self._mensaje(
                "Escribe para buscar en todas las certificaciones."
                if not consulta
                else f"Sin resultados para «{consulta}»."
            )

        self._ajustar_alto()

    def _ajustar_alto(self) -> None:
        """Alto exacto de lista y diálogo, sin dejar hueco que repartir."""
        if self._resultados:
            # Tope de 8 filas: la lista no debe crecer sin freno.
            filas = min(len(self._resultados), 8)
            alto_lista = filas * ALTO_FILA + 8
        else:
            # El mensaje de estado vacío es más alto que una fila normal; si se
            # le da el alto de una fila, el texto se recorta.
            item = self.lista.item(0)
            alto_lista = (item.sizeHint().height() if item else ALTO_FILA) + 8

        self.lista.setFixedHeight(alto_lista)

        # El alto del diálogo se calcula sumando, no preguntando al layout:
        # QLayout.sizeHint() está cacheado y, aun invalidándolo, devolvía el
        # valor del refresco ANTERIOR (12 resultados con la lista ya vacía, y
        # al revés). Sumar los tres bloques es exacto y no depende del caché.
        alto = (
            self._caja_entrada.sizeHint().height()
            + alto_lista
            + self._caja_pie.sizeHint().height()
        )
        # setFixedHeight y no adjustSize: adjustSize conserva el alto previo si
        # es mayor, que era justo el origen del estiramiento.
        self.setFixedHeight(alto)

    def _mensaje(self, texto: str | None) -> None:
        if texto is None:
            return
        item = QListWidgetItem()
        etiqueta = QLabel(texto)
        etiqueta.setObjectName("PaletaVacio")
        etiqueta.setAlignment(Qt.AlignCenter)
        item.setSizeHint(etiqueta.sizeHint())
        item.setFlags(Qt.NoItemFlags)
        self.lista.addItem(item)
        self.lista.setItemWidget(item, etiqueta)

    # ------------------------------------------------------------------

    def _mover(self, delta: int) -> None:
        if not self._resultados:
            return
        fila = self.lista.currentRow() + delta
        self.lista.setCurrentRow(max(0, min(fila, len(self._resultados) - 1)))

    def _ir(self) -> None:
        fila = self.lista.currentRow()
        if 0 <= fila < len(self._resultados):
            entrada = self._resultados[fila]
            self.accept()
            self.navegar.emit(entrada)

    def eventFilter(self, objeto, evento) -> bool:
        if objeto is self.entrada and evento.type() == QEvent.KeyPress:
            assert isinstance(evento, QKeyEvent)
            if evento.key() == Qt.Key_Down:
                self._mover(1)
                return True
            if evento.key() == Qt.Key_Up:
                self._mover(-1)
                return True
            if evento.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._ir()
                return True
        return super().eventFilter(objeto, evento)

    def keyPressEvent(self, evento) -> None:
        if evento.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(evento)
