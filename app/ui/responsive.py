
from __future__ import annotations

from PySide6.QtCore import (
    QEvent, QMargins, QObject, QPoint, QRect, QSize, Qt, QTimer,
)
from PySide6.QtWidgets import (
    QFrame, QLabel, QLayout, QSizePolicy, QVBoxLayout, QWidget,
)

ANCHO_MIN_CARD = 290
ANCHO_MAX_CARD = 440
MAX_COLUMNAS_CARD = 5


def alto_de(widget: QWidget, ancho: int) -> int:
    if widget.isHidden():
        return 0

    ancho = max(int(ancho), 1)

    if widget.hasHeightForWidth():
        alto = widget.heightForWidth(ancho)
        if alto > 0:
            # Se devuelve el alto para ESTE ancho tal cual. No se mezcla con
            # minimumHeight(): ese valor quedó fijado en una medición previa,
            # normalmente con la card más angosta (más líneas de chips), y al
            # combinarlos el contenedor pedía más alto del necesario. El
            # sobrante lo absorbían los QLabel del layout —por eso el badge de
            # estado se estiraba en un bloque alto al desplegar las columnas.
            return alto

    base = max(widget.sizeHint().height(), widget.minimumHeight())

    layout = widget.layout()
    if isinstance(layout, QVBoxLayout):
        base = max(base, alto_vbox(layout, ancho))

    return base


def alto_vbox(layout: QVBoxLayout, ancho: int) -> int:
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

        # Se mide contra el ancho real del widget cuando ya lo tiene.
        # layout.minimumSize() ignora el ancho y devuelve el peor caso
        # (todos los chips en una columna), lo que dejaba un mínimo enorme
        # y un hueco vacío al fondo de la card al desplegar las columnas.
        ancho = widget.width()
        if ancho > 1 and widget.hasHeightForWidth():
            alto = widget.heightForWidth(ancho)
        else:
            alto = layout.minimumSize().height()

        if alto and alto != widget.minimumHeight():
            widget.setMinimumHeight(alto)
            widget.updateGeometry()


class EtiquetaAjustable(QLabel):

    def __init__(self, texto: str = "", parent: QWidget | None = None) -> None:
        super().__init__(texto, parent)
        self.setWordWrap(True)
        politica = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        politica.setHeightForWidth(True)
        self.setSizePolicy(politica)

    def _ancho_util(self) -> int:
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
        if alto > 0 and alto != self.minimumHeight():
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
            self._ajustar()
            self.ajustar_diferido()

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._ajustar()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._ajustar()


def auto_alto(widget: QWidget) -> None:
    if getattr(widget, "_auto_alto", None) is not None:
        return
    filtro = _AutoAlto(widget)
    widget._auto_alto = filtro
    widget.installEventFilter(filtro)
    _AutoAlto._aplicar(widget)


class ChipsFlow(QFrame):
    """Caja con chips que fluyen en horizontal y saltan de línea solos."""

    def __init__(
        self,
        parent: QWidget | None = None,
        espacio_h: int = 6,
        espacio_v: int = 6,
        margenes: QMargins | None = None,
    ) -> None:
        super().__init__(parent)
        self.flow = FlowLayout(
            self,
            margenes=margenes or QMargins(9, 9, 9, 9),
            espacio_h=espacio_h,
            espacio_v=espacio_v,
        )
        politica = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        politica.setHeightForWidth(True)
        self.setSizePolicy(politica)
        self._chips: list[QLabel] = []

    def limpiar(self) -> None:
        for chip in self._chips:
            self.flow.removeWidget(chip)
            chip.setParent(None)
            chip.deleteLater()
        self._chips = []

    def poblar(self, items: list[str], tono: str = "") -> None:
        self.limpiar()
        for texto in items:
            chip = QLabel(texto)
            chip.setObjectName("ChipColumna")
            chip.setProperty("tono", tono)
            chip.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.flow.addWidget(chip)
            self._chips.append(chip)
        self.setProperty("tono", tono)
        self.style().unpolish(self)
        self.style().polish(self)
        self._ajustar()

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, ancho: int) -> int:
        return self.flow.heightForWidth(max(int(ancho), 1))

    def sizeHint(self) -> QSize:
        return QSize(
            self.flow.minimumSize().width(),
            self.heightForWidth(self._ancho_util()),
        )

    def minimumSizeHint(self) -> QSize:
        # Se mide SIEMPRE contra el ancho real disponible, nunca contra
        # self.minimumHeight(): ese valor puede venir de una medición previa
        # con la card más angosta y, al inflar el mínimo del SlotRow, el
        # layout repartía el sobrante estirando el badge de estado.
        if not self._chips:
            return QSize(self.flow.minimumSize().width(), 0)
        return QSize(
            self.flow.minimumSize().width(),
            self.heightForWidth(self._ancho_util()),
        )

    def _ancho_util(self) -> int:
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
        if not self._chips:
            self.setMinimumHeight(0)
            return
        alto = self.heightForWidth(self._ancho_util())
        if alto and alto != self.minimumHeight():
            self.setMinimumHeight(alto)
            self.updateGeometry()

    def ajustar_diferido(self) -> None:
        QTimer.singleShot(0, self._ajustar)

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible)
        if not visible:
            self.setMinimumHeight(0)
        else:
            self._ajustar()
            self.ajustar_diferido()

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._ajustar()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self._ajustar()


class GridResponsivo(QWidget):

    def __init__(
        self,
        ancho_min: int = ANCHO_MIN_CARD,
        espacio: int = 16,
        max_columnas: int = 3,
        ancho_max: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Canvas")
        self._ancho_min = ancho_min
        self._ancho_max = ancho_max
        self._espacio = espacio
        self._max_columnas = max_columnas
        self._columnas = 0
        self._widgets: list[QWidget] = []
        self._recolocando = False
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)


    def agregar(self, widget: QWidget) -> None:
        widget.setParent(self)
        widget.show()
        self._widgets.append(widget)

        senal = getattr(widget, "alto_cambiado", None)
        if senal is not None:
            senal.connect(self.recolocar)

        self.recolocar()

    def widgets(self) -> list[QWidget]:
        return list(self._widgets)

    def columnas_actuales(self) -> int:
        return self._columnas


    def _columnas_para(self, ancho: int, total: int = 0) -> int:
        if ancho <= 0:
            return 1
        cabe = (ancho + self._espacio) // (self._ancho_min + self._espacio)
        columnas = max(1, min(self._max_columnas, int(cabe)))
        if total:
            columnas = min(columnas, total)
        return columnas

    def _anchos(self, ancho: int, columnas: int) -> list[int]:
        base = (ancho - self._espacio * (columnas - 1)) // columnas

        if self._ancho_max and base > self._ancho_max:
            base = self._ancho_max
            return [base] * columnas

        anchos = [base] * columnas
        usado = base * columnas + self._espacio * (columnas - 1)
        anchos[-1] += ancho - usado
        return anchos

    def recolocar(self) -> None:
        if self._recolocando:
            return
        ancho = self.width()
        if ancho <= 0:
            return

        self._recolocando = True
        try:
            for _ in range(2):
                total = self._una_pasada(ancho)
            if self.height() != total or self.minimumHeight() != total:
                self.setFixedHeight(total)
                self.updateGeometry()
        finally:
            self._recolocando = False

    def _una_pasada(self, ancho: int) -> int:
        visibles = [w for w in self._widgets if not w.isHidden()]
        if not visibles:
            return 0

        columnas = self._columnas_para(ancho, len(visibles))
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
                widget.setGeometry(equis[col], y, anchos[col], alturas[col])

            y += max(alturas) + self._espacio
            indice += columnas

        return max(y - self._espacio, 0)


    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self.recolocar()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        self.recolocar()

    def event(self, evento):
        if evento.type() == QEvent.LayoutRequest:
            self.recolocar()
        return super().event(evento)


class FlowLayout(QLayout):

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

    def __del__(self) -> None:
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
        ancho_min = 0
        for item in self._items:
            ancho_min = max(ancho_min, item.minimumSize().width())

        margenes = self.contentsMargins()
        extra_h = margenes.left() + margenes.right()
        extra_v = margenes.top() + margenes.bottom()

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
        QTimer.singleShot(0, self._ajustar)
