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
from PySide6.QtWidgets import (
    QLabel, QLayout, QSizePolicy, QVBoxLayout, QWidget,
)

#: Ancho mínimo legible de una card de fuente.
ANCHO_MIN_CARD = 300


# ---------------------------------------------------------------------------
# Medición determinista de alturas
# ---------------------------------------------------------------------------
#
# Qt calcula la altura mínima de un contenedor sumando los `minimumSizeHint`
# de sus hijos. Para contenido que depende del ancho (QLabel con wordWrap,
# FlowLayout que baja de línea) ese valor está SUBESTIMADO: un QLabel envuelto
# reporta como mínimo una sola línea. Cuando el grid se queda sin espacio
# (2 o 1 columna) usa esos mínimos para dimensionar las filas y las cards
# quedan más bajas que su contenido, que entonces se dibuja por fuera y por
# detrás de la card siguiente.
#
# `alto_de()` / `alto_vbox()` no negocian: calculan el alto REAL para un ancho
# dado, recursivamente. Es la base de `heightForWidth()` en las cards y del
# posicionamiento manual de `GridResponsivo`.


def alto_de(widget: QWidget, ancho: int) -> int:
    """Alto que ocupa `widget` si se le da `ancho` px. 0 si está oculto."""
    if widget.isHidden():
        return 0

    ancho = max(int(ancho), 1)

    if widget.hasHeightForWidth():
        alto = widget.heightForWidth(ancho)
        if alto > 0:
            return max(alto, widget.minimumHeight())

    base = max(widget.sizeHint().height(), widget.minimumHeight())

    # Contenedor sin heightForWidth propio (p. ej. el QFrame de la alerta):
    # se mide su columna interna, que sí puede tener labels envueltos.
    layout = widget.layout()
    if isinstance(layout, QVBoxLayout):
        base = max(base, alto_vbox(layout, ancho))

    return base


def alto_vbox(layout: QVBoxLayout, ancho: int) -> int:
    """Alto real de una columna vertical para un ancho exterior dado."""
    margenes = layout.contentsMargins()
    interior = max(ancho - margenes.left() - margenes.right(), 1)
    espacio = max(layout.spacing(), 0)

    total = 0
    visibles = 0

    for indice in range(layout.count()):
        item = layout.itemAt(indice)

        hijo = item.widget()
        if hijo is not None:
            alto = alto_de(hijo, interior)
        elif item.layout() is not None:
            # Filas horizontales (cabeceras): su alto no depende del ancho.
            alto = item.layout().sizeHint().height()
        else:
            alto = item.sizeHint().height()

        if alto <= 0:
            continue
        total += alto
        visibles += 1

    if visibles > 1:
        total += espacio * (visibles - 1)

    return total + margenes.top() + margenes.bottom()


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
    """Grid de cards con posicionamiento manual y altura determinista.

    No usa `QGridLayout`. La versión anterior sí, y el problema era que Qt
    dimensiona las filas con `minimumSizeHint()` cuando falta espacio: con 2 o
    1 columna las cards recibían menos alto del que su contenido necesita y
    este se dibujaba fuera del `QFrame#Card`, por detrás de la card de abajo.

    Aquí cada card recibe exactamente `alto_de(card, ancho_columna)` y la
    grilla fija su propia altura al total. No hay nada que negociar, así que
    no hay estado intermedio en el que las cosas se solapen.
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
        self._recolocando = False
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    # -- API ------------------------------------------------------------

    def agregar(self, widget: QWidget) -> None:
        widget.setParent(self)
        widget.show()
        self._widgets.append(widget)

        # Las cards avisan cuando cambian de alto (abrir un desplegable,
        # aparecer una alerta). Sin esta señal la grilla no se enteraría,
        # porque ya no depende de la negociación de layouts de Qt.
        senal = getattr(widget, "alto_cambiado", None)
        if senal is not None:
            senal.connect(self.recolocar)

        self.recolocar()

    def widgets(self) -> list[QWidget]:
        return list(self._widgets)

    def columnas_actuales(self) -> int:
        return self._columnas

    # -- Cálculo --------------------------------------------------------

    def _columnas_para(self, ancho: int) -> int:
        if ancho <= 0:
            return 1
        cabe = (ancho + self._espacio) // (self._ancho_min + self._espacio)
        return max(1, min(self._max_columnas, int(cabe)))

    def _anchos(self, ancho: int, columnas: int) -> list[int]:
        """Ancho de cada columna; la última absorbe el resto de la división."""
        base = (ancho - self._espacio * (columnas - 1)) // columnas
        anchos = [base] * columnas
        usado = base * columnas + self._espacio * (columnas - 1)
        anchos[-1] += ancho - usado
        return anchos

    def recolocar(self) -> None:
        """Reposiciona todas las cards. Idempotente y reentrante-seguro."""
        if self._recolocando:
            return
        ancho = self.width()
        if ancho <= 0:
            return

        self._recolocando = True
        try:
            # Dos pasadas: al asignarle su ancho definitivo a una card, sus
            # labels envueltos remiden y el alto puede cambiar. La segunda
            # pasada ya trabaja con las medidas buenas.
            for _ in range(2):
                total = self._una_pasada(ancho)
            if self.height() != total or self.minimumHeight() != total:
                self.setFixedHeight(total)
                self.updateGeometry()
        finally:
            self._recolocando = False

    def _una_pasada(self, ancho: int) -> int:
        # Las cards filtradas no ocupan hueco: se saltan del reparto en vez de
        # dejar un espacio en blanco donde estaban.
        visibles = [w for w in self._widgets if not w.isHidden()]
        if not visibles:
            return 0

        columnas = self._columnas_para(ancho)
        self._columnas = columnas
        anchos = self._anchos(ancho, columnas)

        equis = []
        x = 0
        for ancho_col in anchos:
            equis.append(x)
            x += ancho_col + self._espacio

        y = 0
        indice = 0
        while indice < len(visibles):
            fila = visibles[indice:indice + columnas]

            alturas = [
                alto_de(widget, anchos[col]) for col, widget in enumerate(fila)
            ]

            for col, widget in enumerate(fila):
                # AlignTop: una card corta no se estira para igualar a la más
                # alta de su fila; queda arriba y deja el hueco abajo.
                widget.setGeometry(equis[col], y, anchos[col], alturas[col])

            y += max(alturas) + self._espacio
            indice += columnas

        return max(y - self._espacio, 0)

    # -- Eventos --------------------------------------------------------

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self.recolocar()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self.recolocar()

    def event(self, evento):
        # Un hijo cambió de tamaño ideal (texto nuevo, widget mostrado).
        if evento.type() == QEvent.LayoutRequest:
            self.recolocar()
        return super().event(evento)


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
