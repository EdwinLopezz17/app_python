import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class DatalakeUser:
    id: str = ""
    grupo_entra: str = ""
    displayName: str = ""
    mail: str = ""
    upn: str = ""
    isActive: bool = False
    app_name: str = ""

class DatalakeUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, DatalakeUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.DATALAKE
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Datalake configurado en: {self.path_file}")
            return

        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')

            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                user_id = str(row.get('ID', '')).strip()
                
                if not user_id or user_id.upper() == 'NAN': 
                    continue
                
                _mail = str(row.get('MAIL', '')).strip()
                if not _mail:
                    _mail = str(row.get('USERPRINCIPALNAME', '')).strip()

                if not _mail: 
                    continue

                self._cache[user_id] = DatalakeUser(
                    id=user_id,
                    displayName=str(row.get('DISPLAYNAME', '')).strip(),
                    mail=_mail,
                    upn=str(row.get('USERPRINCIPALNAME', '')).strip(),
                    isActive=True,
                    app_name="Datalake"
                )

            print(f"App Datalake ({self.file_enum.name}) | Total registros en caché: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando el archivo {self.path_file}: {e}")

    def get_all(self) -> list[DatalakeUser]:
        return list(self._cache.values())