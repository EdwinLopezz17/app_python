import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class ExactusPfl:
    grupo: str = ""
    usuario: str = ""
    nombre: str = ""
    isActive: bool = False
    fecha_creacion: str = ""
    tipo: str = ""
    app_name: str = ""

class ExactusPflService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], ExactusPfl] = {}

        self.folder_path = DATA_PATH

        self.file_enum: FileName = FileName.EXACTUS_PERFILES

        nombre_archivo = f"{self.file_enum.value}.csv"
        self.path_file = os.path.join(self.folder_path, nombre_archivo)

        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Exactus configurado en: {self.path_file}")
            return

        try:
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                usuario = str(row.get('USUARIO', '')).strip()
                if not usuario or usuario == 'NAN': 
                    continue
            
                grupo = str(row.get('GRUPO', '')).strip()
                
                cache_key = (usuario.upper(), grupo.upper())
                self._cache[cache_key] = ExactusPfl(
                    grupo = grupo,
                    usuario = usuario,
                    nombre = str(row.get('NOMBRE', '')).strip(),
                    isActive = str(row.get('ESTADO', '')).strip().upper() in ['S'],
                    fecha_creacion = str(row.get('FECHA CREACION', '')).strip(),
                    tipo = str(row.get('TIPO', '')).strip(),
                    app_name = "Exactus"
                )

            print(f"App EXACTUS Perfiles ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[ExactusPfl]:
        return list(self._cache.values())
    