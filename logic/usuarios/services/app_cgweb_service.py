import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class CgwebUser:
    usuario: str = ""
    codcolaborador: str = ""
    nomusrpps: str = ""
    numdoc: str = ""
    isActive: bool = False
    codperfil: str = ""
    stsusrppsaplic: str = ""
    tipousrpps: str = ""
    fechacrea: str = ""
    fecacceso: str = ""
    codaplic: str = ""
    app_name: str = ""

class CgwebUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], CgwebUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.CGWEB
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                usuario = str(row.get('CODUSRPPS', '')).strip().upper()
                if not usuario or usuario == 'NAN': 
                    continue

                codaplic = str(row.get('CODAPLIC', '')).strip()
                cache_key = (usuario, codaplic.upper())

                is_active = str(row.get('STSUSRPPSAPLIC', '')).strip().upper() == "ACT"
                is_active = is_active and str(row.get('STSUSRPPS', '')).strip().upper() == "ACT"

                self._cache[cache_key] = CgwebUser(
                    usuario=str(row.get('CODUSRPPS', '')).strip(),
                    codaplic=codaplic,
                    codcolaborador=str(row.get('CODCOLABORADOR', '')).strip(),
                    nomusrpps=str(row.get('NOMUSRPPS', '')).strip(),
                    numdoc=str(row.get('NUMDOC', '')).strip(),
                    isActive=is_active,
                    codperfil=str(row.get('CODPERFIL', '')).strip(),
                    stsusrppsaplic=str(row.get('STSUSRPPSAPLIC', '')).strip(),
                    tipousrpps=str(row.get('TIPOUSRPPS', '')).strip(),
                    fechacrea=str(row.get('FECHACREA', '')).strip(),
                    fecacceso=str(row.get('FECACCESO', '')).strip(),
                    app_name="CGWEB"
                )

            print(f"App CGWEB ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[CgwebUser]:
        return list(self._cache.values())