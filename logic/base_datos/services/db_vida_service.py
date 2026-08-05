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
class DBVida:
    username: str = ""
    file_name: str = ""
    typee: str = ""
    type_desc: str = ""
    isActive: str = ""
    fecha_login: datetime = None
    fecha_creacion: datetime = None
    fecha_actualizacion: datetime = None
    database_rol: str = ""
    database_name: str = ""
    server_role:str = ""	
    
class DBVidaService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], DBVida] = {}

        self.folder_path = os.path.join(DATA_PATH, "DB Vida")

        self.file_enum: FileName = FileName.DB_VIDA
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        if not lazy:
            self.load_data()

    def load_data(self) -> None:
        self._cache = {}

        if not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurada en: {self.path_file}")
            return
        
        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
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
                self._cache[cache_key] = DBVida(
                    username = username,
                    file_name = file_name,
                    typee = str(row.get("TYPE", "")).strip(),
                    type_desc = str(row.get("TYPE_DESC", "")).strip(),
                    isActive = str(row.get("ISACTIVE", "")).strip().upper() in ["ACTIVO", "ACTIVE"],
                    fecha_login = to_datetime(str(row.get("ULTIMOLOGEO",)).strip(), "DMA"),
                    fecha_creacion = to_datetime(str(row.get("CREATED",)).strip(), "DMA"),
                    fecha_actualizacion = to_datetime(str(row.get("UPDATE",)).strip(), "DMA"),
                    database_rol = str(row.get("DATABASEROLE",)).strip(),
                    database_name = str(row.get("DATABASENAME",)).strip(),
                    server_role = str(row.get("SERVERROLE",)).strip(),
                )

        except Exception as e:
            print(f"Error cargando el archivo {self.path_file}: {e}")

        print(f"DB Vida | Total en caché: {len(self._cache)}")

    def get_all(self) -> list[DBVida]:
        return list(self._cache.values())
    