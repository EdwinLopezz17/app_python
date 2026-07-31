import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class MonokeraUser:
    correo: str = ""
    nombre_usuario: str = ""
    rol: str = ""
    isActive: bool = False
    app_name: str = ""

class MonokeraUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], MonokeraUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.MONOKERA

        nombre_archivo = f"{self.file_enum.value}.csv"
        self.path_file = os.path.join(self.folder_path, nombre_archivo)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Monokera configurado en: {self.path_file}")
            return

        try:
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                correo = str(row.get('CORREO ELECTRÓNICO', '')).strip()
                if not correo or correo == 'NAN': 
                    continue

                rol = str(row.get('ROLES', '')).strip()
                
                cache_key = (correo.upper(), rol.upper())
                self._cache[cache_key] = MonokeraUser(
                    correo=correo,
                    nombre_usuario=str(row.get('NOMBRE DEL USUARIO', '')).strip(),
                    rol=rol,
                    isActive=str(row.get('ESTADO', '')).strip().upper() in ["ACTIVO", "1", "1.0", "TRUE"],
                    app_name="Monokera",
                )

            print(f"App Monokera ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[MonokeraUser]:
        return list(self._cache.values())