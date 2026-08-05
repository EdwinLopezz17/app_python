import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class BotmakerUser:
    email: str = ""
    rol: str = ""
    isActive: bool = False
    registration_date: str = ""
    lastlogin_date: str = ""
    app_name: str = ""

class BotmakerUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], BotmakerUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.BOTMAKER
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
                email = str(row.get('EMAIL', '')).strip()
                if not email or email == 'NAN': 
                    continue

                rol = str(row.get('ROLE', '')).strip()
                
                cache_key = (email.upper(), rol.upper())
                self._cache[cache_key] = BotmakerUser(
                    email = email,
                    rol = rol,
                    isActive=str(row.get('ACTIVE', '')).strip().upper() in ["TRUE", "1", "1.0", "ACTIVO", "VERDADERO"],
                    registration_date=str(row.get('REGISTRATION_DATE', '')).strip(),
                    lastlogin_date=str(row.get('LAST_LOGIN_DATE', '')).strip(),
                    app_name="Botmaker"
                )

            print(f"App Botmaker ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[BotmakerUser]:
        return list(self._cache.values())