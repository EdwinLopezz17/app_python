import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class PmsUser:
    empresa_login: str = ""
    usuario: str = ""
    descripcion_login: str = ""
    codigo_identidad: str = ""
    privilegio: str = ""
    perfil: str = ""
    estado: str = ""
    login_windows: str = ""
    isActive: bool = False
    fecha_expiracion: str = ""
    app_name: str = ""

class PmsUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, PmsUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.PMS
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de PMS configurado en: {self.path_file}")
            return

        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                usuario = str(row.get('LOGIN_SISTEMA', '')).strip()
                if not usuario or usuario == 'NAN':
                    continue
                
                self._cache[usuario.upper()] = PmsUser(
                    empresa_login=str(row.get('EMPRESA_LOGIN', '')).strip(),
                    usuario = usuario,
                    descripcion_login=str(row.get('DESCRIPCION_LOGIN', '')).strip(),
                    codigo_identidad=str(row.get('CODIGO_IDENTIDAD', '')).strip(),
                    privilegio=str(row.get('PRIVILEGIO', '')).strip(),
                    perfil=str(row.get('PERFIL', '')).strip(),
                    estado=str(row.get('ESTADO', '')).strip(),
                    login_windows=str(row.get('LOGIN_WINDOWS', '')).strip(),
                    isActive=not str(row.get('ACTIVO_BLOQUEADO', '')).strip().upper() in ["BLOQUEADO", "FALSE", "0", "0.0"],
                    fecha_expiracion=str(row.get('FECHA_EXPIRACION', '')).strip(),
                    app_name="PMS",

                )

            print(f"App PMS ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[PmsUser]:
        return list(self._cache.values())