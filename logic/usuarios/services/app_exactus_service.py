import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class ExactusUser:
    usuario: str = ""
    isActive: bool = False
    createdby: str = ""
    nombre_completo: str = ""
    createdate: str = ""
    updatedby: str = ""
    app_name: str = ""

class ExactusUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, ExactusUser] = {}

        self.folder_path = DATA_PATH

        self.file_enum: FileName = FileName.EXACTUS

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
                
                self._cache[usuario.upper()] = ExactusUser(
                    usuario = usuario,
                    isActive=str(row.get('ACTIVO', '')).strip().upper() in ['SI', 'YES', 'TRUE', '1', "1.0", 'S', 'ACTIVO'],
                    createdby=str(row.get('CREATEDBY', '')).strip(),
                    nombre_completo=str(row.get('NOMBRE', '')).strip(),
                    createdate=str(row.get('CREATEDATE', '')).strip(),
                    updatedby=str(row.get('UPDATEDBY', '')).strip(),
                    app_name = "Exactus"
                )

            print(f"App EXACTUS ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[ExactusUser]:
        return list(self._cache.values())