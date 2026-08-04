import pandas as pd
import os
import re
from datetime import date, datetime, time

def to_datetime(val, format=None) -> datetime | None:
    if val is None or pd.isna(val):
        return None

    ts = None

    if format is not None:
        try:
            if format == "DMA":
                ts = pd.to_datetime(val, dayfirst=True, format='mixed', errors='coerce')
            elif format == "MDA":
                ts = pd.to_datetime(val, dayfirst=False, format='mixed', errors='coerce')
            else:
                ts = pd.to_datetime(val, format='mixed', errors='coerce')
        except Exception:
            pass

    if ts is None or pd.isna(ts):
        if hasattr(val, 'date'):
            try:
                ts = pd.Timestamp(val)
            except Exception:
                return None
        else:
            try:
                ts = pd.to_datetime(val, format='mixed', errors='coerce')
            except Exception:
                return None

    if ts is None or pd.isna(ts) or ts.year < 1900:
        return None

    dt = ts.to_pydatetime()

    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)

    # Si la fecha no tiene horas, minutos ni segundos, se asume el fin del día (23:59:59)
    if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.microsecond == 0:
        if not _original_has_time(val):
            return datetime.combine(dt.date(), time(23, 59, 59))

    return dt

def _original_has_time(val) -> bool:
    if isinstance(val, datetime):
        return True
    if isinstance(val, date) and not isinstance(val, datetime):
        return False
    if isinstance(val, str):
        return bool(re.search(r'\d{1,2}:\d{2}', val))
    return False

def delete_file(path_file: str) -> bool:
        try:
            if path_file and os.path.exists(path_file):
                os.remove(path_file)
                print(f"Archivo eliminado: {path_file}")

                return True

        except Exception as e:
            print(f"Warning: Error al intentar eliminar el archivo {path_file}: {e}")
            return False
