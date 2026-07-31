import os
from dataclasses import dataclass
import pandas as pd
from dotenv import load_dotenv
import datetime
from models.file_names import FileName
from logic.share.utils import to_datetime

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class DBGenerales:
    username: str = ""
    file_name: str = ""
    isActive: str = ""
    fecha_bloqueo: datetime = None
    fecha_creacion: datetime = None
    profile: str = ""
    fecha_login: datetime = None

class DBGeneralesService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], DBGenerales] = {}

        self.folder_path = os.path.join(DATA_PATH, "DB Generales")

        self.file_enum: FileName = FileName.DB_GENERALES

        nombre_archivo = f"{self.file_enum.value}.csv"
        self.path_file = os.path.join(self.folder_path, nombre_archivo)

        if not lazy:
            self.load_data()

    def load_data(self) -> None:
        self._cache = {}

        if not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurada en: {self.path_file}")
            return
        
        try:
            df = pd.read_csv(self.path_file, sep=";", encoding="utf-8").fillna("")
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                username = str(row.get("USERNAME", "")).strip()
                raw_file_name = str(row.get("ORIGIN_FILE", "")).strip()

                if not username or username.upper() == "NAN":
                    continue

                if '.' in raw_file_name:
                    file_name, _, _ = raw_file_name.rpartition('.')
                else:
                    file_name = raw_file_name

                cache_key = (username.upper(), file_name.upper())
                self._cache[cache_key] = DBGenerales(
                    username = username,
                    file_name = file_name,
                    isActive = "LOCKED" not in str(row.get("ACCOUNT_STATUS", "")).strip().upper(),
                    fecha_bloqueo = to_datetime(str(row.get("LOCK_DATE",)).strip(), "DMA"),
                    fecha_creacion = to_datetime(str(row.get("CREATED",)).strip(), "DMA"),
                    profile = str(row.get("PROFILE", "")).strip(),
                    fecha_login = to_datetime(str(row.get("ULTIMO_LOGIN",)).strip(), "DMA"),
                )

        except Exception as e:
            print(f"Error cargando el archivo {self.path_file}: {e}")

        print(f"DB Generales| Total en caché: {len(self._cache)}")

    def get_all(self) -> list[DBGenerales]:
        return list(self._cache.values())
    