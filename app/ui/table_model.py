from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.catalog import display


class DataFrameModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame | None = None, modelo: str | None = None) -> None:
        super().__init__()
        self._original = df if df is not None else pd.DataFrame()
        self._df = self._original
        self._etiquetas = display.etiquetas(modelo) if modelo else {}

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        valor = self._df.iat[index.row(), index.column()]

        if role == Qt.DisplayRole:
            if valor is None or (isinstance(valor, float) and pd.isna(valor)):
                return ""
            if isinstance(valor, bool):
                return "Sí" if valor else "No"
            if isinstance(valor, pd.Timestamp):
                return valor.strftime("%d/%m/%Y %H:%M")
            return str(valor)

        if role == Qt.TextAlignmentRole:
            if isinstance(valor, bool):
                return int(Qt.AlignCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            campo = str(self._df.columns[section])
            return self._etiquetas.get(campo, campo)
        return str(section + 1)

    def set_dataframe(self, df: pd.DataFrame, modelo: str | None = None) -> None:
        self.beginResetModel()
        self._original = df
        self._df = df
        if modelo is not None:
            self._etiquetas = display.etiquetas(modelo)
        self.endResetModel()

    def aplicar_filtro(self, texto: str) -> None:
        texto = (texto or "").strip()
        self.beginResetModel()
        if not texto:
            self._df = self._original
        else:
            partes = [
                self._original[c].astype(str).str.contains(texto, case=False, na=False, regex=False)
                for c in self._original.columns
            ]
            if partes:
                mascara = partes[0]
                for p in partes[1:]:
                    mascara |= p
                self._df = self._original[mascara]
            else:
                self._df = self._original
        self.endResetModel()

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    @property
    def total_original(self) -> int:
        return len(self._original)
