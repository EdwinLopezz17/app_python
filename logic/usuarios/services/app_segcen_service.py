import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class SegcenUser:
    id_usuario: str = ""
    apellido_paterno: str = ""
    apellido_materno: str = ""
    nombres: str = ""
    email: str = ""
    fecha_creacion: str = ""
    fecha_modificacion: str = ""
    isActive: bool = False
    id_rol: str = ""
    nombre_rol: str = ""
    app_name: str = ""

class SegcenUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], SegcenUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.SEGCEN

        nombre_archivo = self.file_enum.value
        self.path_file = os.path.join(self.folder_path, nombre_archivo)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de SEGCEN configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                id_usuario = str(row.get('ID USUARIO', '')).strip().upper()
                if not id_usuario or id_usuario == 'NAN': 
                    continue

                id_rol = str(row.get('ID ROL', '')).strip()
                
                cache_key = (id_usuario, id_rol.upper())

                self._cache[cache_key] = SegcenUser(
                    id_usuario=str(row.get('ID USUARIO', '')).strip(),
                    apellido_paterno=str(row.get('APELLIDO PATERNO', '')).strip(),
                    apellido_materno=str(row.get('APELLIDO MATERNO', '')).strip(),
                    nombres=str(row.get('NOMBRES', '')).strip(),
                    email=str(row.get('EMAIL', '')).strip(),
                    fecha_creacion=str(row.get('FECHA DE CREACIÓN', '')).strip(),
                    fecha_modificacion=str(row.get('FECHA DE MODIFICACIÓN', '')).strip(),
                    isActive = str(row.get('ESTADO', '')).strip().upper() in ['ACTIVO', '1', "1.0", 'TRUE', "VERDADERO"],
                    id_rol=id_rol,
                    nombre_rol=str(row.get('NOMBRE DE ROL', '')).strip(),
                    app_name="Segcen"
                )

            print(f"App SEGCEN ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[SegcenUser]:
        return list(self._cache.values())