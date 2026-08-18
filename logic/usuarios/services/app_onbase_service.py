import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class OnbaseUser:
    usuario: str = ""
    nombre_completo: str = ""
    correo: str = ""
    grupo_onbase: str = ""
    ultimo_logueo: str = ""
    isActive: bool = False
    app_name: str = ""

class OnbaseUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], OnbaseUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.ONBASE
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Onbase configurado en: {self.path_file}")
            return

        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                usuario = str(row.get('USUARIO', '')).strip()
                if not usuario or usuario == 'NAN': 
                    continue
                
                grupo_onbase = str(row.get('GRUPOONBASE', '')).strip()
                
                cache_key = (usuario.upper(), grupo_onbase.upper())
                self._cache[cache_key] = OnbaseUser(
                    usuario = usuario,
                    nombre_completo=str(row.get('NOMBRECOMPLETO', '')).strip(),
                    correo=str(row.get('CORREO', '')).strip(),
                    grupo_onbase = grupo_onbase,
                    ultimo_logueo=str(row.get('ULTIMOLOGUEO', '')).strip(),
                    isActive=True,
                    app_name="OnBase",
                )

            print(f"App ONBASE ({self.file_enum.name}) | Total registros (Usuario-Grupo) en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[OnbaseUser]:
        return list(self._cache.values())