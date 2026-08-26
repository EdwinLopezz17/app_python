import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class SsaUser:
    app_name: str = ""
    usuario: str = ""
    cod_colab: str = ""
    nombre_colab: str = ""
    mail: str = ""
    isActive: bool = False

class SsaUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, SsaUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.SSA
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de SEGCEN configurado en: {self.path_file}")
            return

        try:
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                usuario = str(row.get('CODUSRPPS', ''))
                if not usuario: 
                    continue

                self._cache[usuario.upper()] = SsaUser(
                    usuario = usuario,
                    cod_colab = str(row.get('CODCOLABORADOR', '')).strip(),
                    nombre_colab = str(row.get('NOMUSRPPS', '')).strip(),
                    mail = str(row.get('MAIL', '')).strip(),
                    isActive = str(row.get('STSUSRPPS', '')).strip().upper() in ["ACT"],
                    app_name="SSA"
                )

            print(f"App SSA cargada ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[SsaUser]:
        return list(self._cache.values())
    