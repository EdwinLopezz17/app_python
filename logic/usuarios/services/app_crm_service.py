import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class CRMUser:
    id: str = ""
    grupo_entra: str = ""
    displayName: str = ""
    mail: str = ""
    upn: str = ""
    isActive: bool = False
    app_name: str = ""

class CRMUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, CRMUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.CRM
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)

        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de CRM configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
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

                self._cache[user_id] = CRMUser(
                    id=user_id,
                    displayName=str(row.get('DISPLAYNAME', '')).strip(),
                    mail=_mail,
                    upn=str(row.get('USERPRINCIPALNAME', '')).strip(),
                    isActive=True,
                    app_name="CRM",
                )

            print(f"App CRM ({self.file_enum.name}) | Total registros en caché: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando el archivo {self.path_file}: {e}")

    def get_all(self) -> list[CRMUser]:
        return list(self._cache.values())
    