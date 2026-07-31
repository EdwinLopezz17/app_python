import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class DNIUserInfo:
    username: str = ""
    tipo_usuario: str = ""
    usuario: str = ""
    dni: str = ""
    comentario: str = ""

class DNIUserService():
    def __init__(self, lazy: bool = False):
        self._cache: dict[str, DNIUserInfo] = {}
        self._cache_by_dni: dict[str, list[DNIUserInfo]] = {}
        
        self.folder_path = DATA_PATH
        self.file_enum: FileName = FileName.DNI_VS_USUARIOS
        nombre_archivo = self.file_enum.value
        self.path_file = os.path.join(self.folder_path, nombre_archivo)
        
        if not lazy:
            self.load_data()

    def load_data(self) -> None:
        self._cache = {}
        self._cache_by_dni = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de DNI vs Usuarios configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                username = str(row.get('USERNAME', '')).strip().upper()
                if not username or username == 'NAN': 
                    continue

                dni_raw = str(row.get('DNI', '')).strip()
                dni_key = dni_raw.upper()

                user_info = DNIUserInfo(
                    username=str(row.get('USERNAME', '')).strip(),
                    tipo_usuario=str(row.get('TIPO', '')).strip(),
                    usuario=str(row.get('USUARIO', '')).strip(),
                    dni=dni_raw, 
                    comentario=str(row.get('COMENTARIO', '')).strip()
                )

                self._cache[username] = user_info

                if dni_key:
                    if dni_key not in self._cache_by_dni:
                        self._cache_by_dni[dni_key] = []
                    self._cache_by_dni[dni_key].append(user_info)

            print(f"DNI vs Usuarios ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def delete_file(self) -> bool:
        delete_file(self.path_file)
        self._cache.clear()
        self._cache_by_dni.clear()
        return True

    def get_by_username(self, username: str) -> DNIUserInfo | None:
        key = str(username).strip().upper() if username else ""
        return self._cache.get(key)
    
    def get_by_dni(self, dni: str) -> list[DNIUserInfo]:
        key = str(dni).strip().upper() if dni else ""
        return self._cache_by_dni.get(key, [])
    
    def get_all(self) -> list[DNIUserInfo]:
        return list(self._cache.values())
    