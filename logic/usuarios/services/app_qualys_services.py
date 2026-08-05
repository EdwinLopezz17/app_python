import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class QualysUser:
    email: str = ""
    role: str = ""
    nombre: str = ""
    isActive: bool = False
    created_at: datetime = None
    last_login: datetime = None
    app_name: str = ""

class QualysUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[tuple[str, str], QualysUser] = {}
        self.folder_path = DATA_PATH

        self.file_enum: FileName = FileName.QUALYS
        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Qualys configurado en: {self.path_file}")
            return

        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=';', encoding='utf-8').fillna('')
            
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                email = str(row.get('EMAIL', '')).strip()
                if not email or email == 'NAN': 
                    continue

                role = str(row.get('ROLE', '')).strip()

                created_raw = str(row.get('CREATED', '')).strip()
                last_login_raw = str(row.get('LAST LOGIN', '')).strip()

                def parse_qualys_date(date_str: str) -> datetime | None:
                    if not date_str or date_str.upper() in ['NAN', '']:
                        return None
                    clean_str = date_str.replace(" at ", " ").split(" (")[0].strip()
                    
                    return to_datetime(clean_str, format="MDA")

                created_dt = parse_qualys_date(created_raw)
                last_login_dt = parse_qualys_date(last_login_raw)

                cache_key = (email.upper(), role.upper())
                self._cache[cache_key] = QualysUser(
                    email=email,
                    role=role,
                    nombre=str(row.get('NAME', '')).strip(),
                    isActive=str(row.get('STATUS', '')).strip().upper() in ["ACTIVE", "TRUE", "1", "ACTIVO"],
                    created_at=created_dt,
                    last_login=last_login_dt,
                    app_name="Qualys"
                )

            print(f"App Qualys ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[QualysUser]:
        return list(self._cache.values())
    