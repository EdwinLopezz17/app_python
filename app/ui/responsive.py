"""Layouts que se reacomodan solos según el ancho disponible.

Equivalente en Qt de lo que en el Next.js hacía Tailwind con
`grid-cols-1 sm:grid-cols-2 xl:grid-cols-3` y con `flex-wrap` en la barra de
acciones. La app se usa a media pantalla en monitores Full HD (~960 px), así
que nada puede depender de que la ventana esté maximizada.
"""

from __future__ import annotations

from PySide6.QtCore import QMargins, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QGridLayout, QLayout, QSizePolicy, QWidget

#: Ancho mínimo legible de una card de fuente.
ANCHO_MIN_CARD = 300


class GridResponsivo(QWidget):
    """Grid que recalcula el número de columnas cada vez que cambia el ancho.

    Las columnas se reparten el espacio por igual (todas con stretch 1), así
    las cards siempre quedan alineadas y del mismo tamaño, en vez de quedar
    ragged como pasaría con un flow puro.
    """

    def __init__(
        self,
        ancho_min: int = ANCHO_MIN_CARD,
        espacio: int = 16,
        max_columnas: int = 3,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Canvas")
        self._ancho_min = ancho_min
        self._espacio = espacio
        self._max_columnas = max_columnas
        self._columnas = 0
        self._widgets: list[QWidget] = []

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(espacio)
        self._grid.setVerticalSpacing(espacio)

    def agregar(self, widget: QWidget) -> None:
        self._widgets.append(widget)
        self._recolocar(forzar=True)

    def widgets(self) -> list[QWidget]:
        return list(self._widgets)

    def columnas_actuales(self) -> int:
        return self._columnas

    def _columnas_para(self, ancho: int) -> int:
        if ancho <= 0:
            return 1
        cabe = (ancho + self._espacio) // (self._ancho_min + self._espacio)
        return max(1, min(self._max_columnas, int(cabe)))

    def _recolocar(self, forzar: bool = False) -> None:
        columnas = self._columnas_para(self.width())
        if columnas == self._columnas and not forzar:
            return
        self._columnas = columnas

        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self)

        for indice, widget in enumerate(self._widgets):
            # AlignTop: una card corta no se estira para igualar a la más alta
            # de su fila; queda arriba y deja el hueco abajo.
            self._grid.addWidget(
                widget, indice // columnas, indice % columnas, Qt.AlignTop
            )

        for col in range(self._max_columnas):
            self._grid.setColumnStretch(col, 1 if col < columnas else 0)
            self._grid.setColumnMinimumWidth(col, 0)

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._recolocar()


class FlowLayout(QLayout):
    """Layout horizontal que baja de línea cuando no hay espacio.

    Se usa en las barras de acciones: con la ventana a media pantalla los
    botones se apilan en dos filas en vez de recortarse o desbordarse.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        margenes: QMargins | None = None,
        espacio_h: int = 8,
        espacio_v: int = 8,
    ) -> None:
        super().__init__(parent)
        self._items: list = []
        self._espacio_h = espacio_h
        self._espacio_v = espacio_v
        self.setContentsMargins(margenes or QMargins(0, 0, 0, 0))

    def __del__(self) -> None:  # pragma: no cover - limpieza de Qt
        while self._items:
            self._items.pop()

    def addItem(self, item) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, indice: int):
        if 0 <= indice < len(self._items):
            return self._items[indice]
        return None

    def takeAt(self, indice: int):
        if 0 <= indice < len(self._items):
            return self._items.pop(indice)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, ancho: int) -> int:
        return self._acomodar(QRect(0, 0, ancho, 0), solo_medir=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._acomodar(rect, solo_medir=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        tamano = QSize()
        for item in self._items:
            tamano = tamano.expandedTo(item.minimumSize())
        margenes = self.contentsMargins()
        return tamano + QSize(
            margenes.left() + margenes.right(),
            margenes.top() + margenes.bottom(),
        )

    def _acomodar(self, rect: QRect, solo_medir: bool) -> int:
        margenes = self.contentsMargins()
        area = rect.adjusted(
            margenes.left(), margenes.top(), -margenes.right(), -margenes.bottom()
        )
        x, y, alto_linea = area.x(), area.y(), 0

        for item in self._items:
            tamano = item.sizeHint()
            siguiente = x + tamano.width() + self._espacio_h
            if siguiente - self._espacio_h > area.right() and alto_linea > 0:
                x = area.x()
                y = y + alto_linea + self._espacio_v
                siguiente = x + tamano.width() + self._espacio_h
                alto_linea = 0

            if not solo_medir:
                item.setGeometry(QRect(QPoint(x, y), tamano))

            x = siguiente
            alto_linea = max(alto_linea, tamano.height())

        return y + alto_linea - rect.y() + margenes.bottom()


class ContenedorFlow(QWidget):
    """`QWidget` con `FlowLayout` que reporta bien su alto (heightForWidth)."""

    def __init__(
        self,
        parent: QWidget | None = None,
        espacio_h: int = 8,
        espacio_v: int = 8,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Canvas")
        self.flow = FlowLayout(self, espacio_h=espacio_h, espacio_v=espacio_v)
        politica = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        politica.setHeightForWidth(True)
        self.setSizePolicy(politica)

    def agregar(self, widget: QWidget) -> None:
        self.flow.addWidget(widget)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, ancho: int) -> int:
        return self.flow.heightForWidth(ancho)

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), self.flow.heightForWidth(self.width()))

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self.setMinimumHeight(self.flow.heightForWidth(self.width()))
