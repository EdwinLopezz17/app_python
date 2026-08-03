from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QHeaderView

from app.catalog.colors import GrupoColor

ALTO = 34
MARGEN = 12


class CabeceraColoreada(QHeaderView):
    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Horizontal, parent)
        self.setSectionsClickable(True)
        self.setHighlightSections(False)
        self.setFixedHeight(ALTO)
        self.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    def _grupo(self, indice: int) -> GrupoColor | None:
        modelo = self.model()
        obtener = getattr(modelo, "grupo_de_columna", None)
        return obtener(indice) if obtener else None

    def paintSection(self, painter: QPainter, rect, indice: int) -> None:
        grupo = self._grupo(indice)
        if grupo is None:
            super().paintSection(painter, rect, indice)
            return

        painter.save()
        painter.fillRect(rect, QColor(grupo.fill))

        fuente = QFont(painter.font())
        fuente.setBold(True)
        fuente.setPointSizeF(max(fuente.pointSizeF() - 1, 7.0))
        painter.setFont(fuente)
        painter.setPen(QColor(grupo.text))

        texto = str(self.model().headerData(indice, Qt.Horizontal, Qt.DisplayRole) or "")
        area = rect.adjusted(MARGEN, 0, -MARGEN, 0)
        elidido = painter.fontMetrics().elidedText(texto, Qt.ElideRight, area.width())
        painter.drawText(area, Qt.AlignLeft | Qt.AlignVCenter, elidido)
        painter.restore()
