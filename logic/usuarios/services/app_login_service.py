import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class AppLogin:
    usuario: str = ""
    app_name: str = ""
    ultimo_logueo: datetime = None

class AppLoginService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], AppLogin] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.APP_LOGIN
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Onbase configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                usuario = str(row.get('IDUSUARIO', '')).strip()
                if not usuario or usuario == 'NAN': 
                    continue
                
                app_name = str(row.get('NOMBRE_APLICACION', '')).strip()
                
                cache_key = (usuario.upper(), app_name.upper())
                self._cache[cache_key] = AppLogin(
                    usuario = usuario,
                    ultimo_logueo=to_datetime(str(row.get('ULTIMOLOGEO', '')).strip()),
                    app_name=app_name,
                )

            print(f"App LOGIN ({self.file_enum.name}) | Total registros en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[AppLogin]:
        return list(self._cache.values())
    
    def get_by_user_and_app(self, usuario: str, app_name: str) -> AppLogin | None:
        if not usuario or not app_name:
            return None
            
        cache_key = (usuario.strip().upper(), app_name.strip().upper())
        return self._cache.get(cache_key, None)
