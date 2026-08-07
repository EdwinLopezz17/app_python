"""Layouts que se reacomodan solos según el ancho disponible.

Equivalente en Qt de lo que en el Next.js hacía Tailwind con
`grid-cols-1 sm:grid-cols-2 xl:grid-cols-3` y con `flex-wrap` en la barra de
acciones. La app se usa a media pantalla en monitores Full HD (~960 px), así
que nada puede depender de que la ventana esté maximizada.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEvent, QMargins, QObject, QPoint, QRect, QSize, Qt, QTimer,
)
from PySide6.QtWidgets import QGridLayout, QLabel, QLayout, QSizePolicy, QWidget

#: Ancho mínimo legible de una card de fuente.
ANCHO_MIN_CARD = 300


class _AutoAlto(QObject):
    """Fija `minimumHeight` al alto que realmente pide el layout del widget.

    Qt negocia la altura con `sizeHint()`/`minimumSizeHint()`, que son
    *sugerencias*: un `QGridLayout` sin espacio suficiente las ignora y recorta
    al hijo. Con contenido que depende del ancho (QLabel con `wordWrap`,
    `FlowLayout` que baja de línea) esa negociación se queda con valores viejos
    y la card acaba más baja de lo que necesita: el contenido se ve cortado.

    `minimumHeight` sí es un límite duro. Se recalcula en cada `LayoutRequest`,
    que es el evento que Qt manda cuando un hijo cambia de tamaño ideal.
    """

    def eventFilter(self, obj: QWidget, evento) -> bool:
        if evento.type() == QEvent.LayoutRequest:
            self._aplicar(obj)
        return False

    @staticmethod
    def _aplicar(widget: QWidget) -> None:
        layout = widget.layout()
        if layout is None:
            return
        layout.invalidate()
        alto = layout.minimumSize().height()
        if alto and alto != widget.minimumHeight():
            widget.setMinimumHeight(alto)
            widget.updateGeometry()


class EtiquetaAjustable(QLabel):
    """`QLabel` con `wordWrap` que sí reserva el alto que necesita.

    Un `QLabel` envuelto tiene `heightForWidth`, pero para que el layout padre
    lo consulte hace falta que TODOS los ancestros lleven el flag
    `heightForWidth` en su `sizePolicy`. En una card con varios niveles de
    `QVBoxLayout` esa cadena se rompe y el texto largo se corta a una línea.

    Aquí se resuelve por abajo: la propia etiqueta fija su `minimumHeight`
    (que sí es un límite duro) cada vez que cambia de ancho o de texto.
    """

    def __init__(self, texto: str = "", parent: QWidget | None = None) -> None:
        super().__init__(texto, parent)
        self.setWordWrap(True)
        politica = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        politica.setHeightForWidth(True)
        self.setSizePolicy(politica)

    def _ancho_util(self) -> int:
        """Ancho con el que medir el texto envuelto.

        `self.width()` todavía es el ancho viejo (o 0) justo después de un
        `setVisible(True)`, antes de que Qt corra el pase de layout. Medir con
        él daba una altura calculada para otro ancho y el texto se desbordaba
        fuera de la card. El `contentsRect()` del padre ya es correcto en ese
        momento, así que se usa como referencia.
        """
        propio = self.width()
        padre = self.parentWidget()
        if padre is not None:
            layout = padre.layout()
            margen = 0
            if layout is not None:
                m = layout.contentsMargins()
                margen = m.left() + m.right()
            del_padre = padre.contentsRect().width() - margen
            if del_padre > 0 and (propio <= 1 or abs(del_padre - propio) > 2):
                return del_padre
        return max(propio, 1)

    def _ajustar(self) -> None:
        if not self.isVisibleTo(self.parentWidget() or self):
            return
        alto = self.heightForWidth(self._ancho_util())
        if alto and alto != self.minimumHeight():
            self.setMinimumHeight(alto)
            self.updateGeometry()

    def ajustar_diferido(self) -> None:
        QTimer.singleShot(0, self._ajustar)

    def setText(self, texto: str) -> None:
        super().setText(texto)
        self._ajustar()

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible)
        if not visible:
            self.setMinimumHeight(0)
        else:
            # Diferido: en este punto el widget aún no tiene el ancho final.
            self._ajustar()
            self.ajustar_diferido()

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._ajustar()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._ajustar()


def auto_alto(widget: QWidget) -> None:
    """Engancha `_AutoAlto` al widget (idempotente)."""
    if getattr(widget, "_auto_alto", None) is not None:
        return
    filtro = _AutoAlto(widget)
    widget._auto_alto = filtro
    widget.installEventFilter(filtro)
    _AutoAlto._aplicar(widget)


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
        # SetMinimumSize hace que el propio QGridLayout empuje su minimumSize
        # al widget contenedor en cada LayoutRequest. Sin esto la altura solo
        # se recalculaba en `_recolocar()` (o sea, solo al cambiar el ancho) y
        # una card que crecía sin cambiar de ancho -- al abrir un desplegable o
        # al aparecer la alerta roja -- se salía de su fila y se dibujaba por
        # debajo de la card siguiente.
        self._grid.setSizeConstraint(QLayout.SetMinimumSize)
        auto_alto(self)

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

        self._grid.invalidate()
        alto = self._grid.minimumSize().height()
        if alto and alto != self.minimumHeight():
            self.setMinimumHeight(alto)
        self.updateGeometry()

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
        """Alto real del flow, no el del ítem más alto.

        La versión anterior devolvía `expandedTo(item.minimumSize())`, es decir
        la altura de UN solo botón aunque el flow hubiera bajado a dos o tres
        líneas. El `QVBoxLayout` de la card consultaba ese valor y reservaba
        una sola fila: los botones de la segunda línea se pintaban fuera del
        `QFrame#Card` y quedaban por detrás de la card de abajo.
        """
        ancho_min = 0
        for item in self._items:
            ancho_min = max(ancho_min, item.minimumSize().width())

        margenes = self.contentsMargins()
        extra_h = margenes.left() + margenes.right()
        extra_v = margenes.top() + margenes.bottom()

        # El ancho útil real manda; si el layout todavía no tiene geometría
        # (primer pase) se cae al ancho mínimo de un ítem, que es el peor caso
        # (todo apilado) y por tanto nunca se queda corto.
        padre = self.parentWidget()
        ancho_padre = padre.width() if padre is not None else 0
        ancho = max(self.geometry().width(), ancho_padre, ancho_min + extra_h, 1)
        alto = self._acomodar(QRect(0, 0, ancho, 0), solo_medir=True)

        return QSize(ancho_min + extra_h, max(alto, extra_v))

    def minimumSizeHint(self) -> QSize:
        return self.minimumSize()

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

    def minimumSizeHint(self) -> QSize:
        return QSize(self.flow.minimumSize().width(), self.minimumHeight())

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._ajustar()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._ajustar()

    def _ajustar(self) -> None:
        alto = self.flow.heightForWidth(max(self.width(), 1))
        if alto and alto != self.minimumHeight():
            self.setMinimumHeight(alto)
            self.updateGeometry()

    def ajustar_diferido(self) -> None:
        """Reajusta en el siguiente ciclo de eventos.

        Útil cuando algo cambia el contenido antes de que Qt haya asignado
        geometría: medir en ese instante usa el ancho viejo.
        """
        QTimer.singleShot(0, self._ajustar)
