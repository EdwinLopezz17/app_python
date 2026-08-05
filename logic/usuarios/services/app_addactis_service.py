import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class AddactisUser:
    username: str = ""
    userdomain: str = ""
    isActive: bool = False 
    app_name: str = ""

class AddactisUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], AddactisUser] = {}
        self.folder_path = DATA_PATH

        self.file_enum: FileName = FileName.ADDACTIS
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo configurado en: {self.path_file}")
            return

        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                username = str(row.get('USER NAME', '')).strip()
                if not username or username == 'NAN': 
                    continue

                userdomain = str(row.get('USER DOMAIN', '')).strip()
                
                cache_key = (username.upper(), userdomain.upper())
                self._cache[cache_key] = AddactisUser(
                    username=username,
                    userdomain=userdomain,
                    isActive=True,
                    app_name ="Addactis"
                )

            print(f"App Addactis ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")
    
    def get_all(self) -> list[AddactisUser]:
        return list(self._cache.values())
    