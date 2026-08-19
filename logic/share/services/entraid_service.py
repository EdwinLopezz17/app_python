import os
import json
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class EntraUser:
    id: str = ""
    upn: str = ""
    email: str = ""
    isActive: bool = False
    fechaCreacion: datetime = None
    lastSignInDateTime: datetime = None
    lastNonInteractiveSignInDateTime: datetime = None
    lastActivityDateTime: datetime = None
    dni: str = ""
    rol: str = ""
    jefe: str = ""

class EntraUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, EntraUser] = {}
        self._cache_email: dict[str, EntraUser] = {}
        self._cache_upn: dict[str, EntraUser] = {}
        
        self.folder_path = DATA_PATH

        self.file_enum: FileName = FileName.ENTRA_ID

        self.path_file = os.path.join(self.folder_path, self.file_enum.value)
        
        if not lazy:
            self.cargar_datos()

    def _parse_datetime(self, date_str: str) -> datetime | None:
        if not date_str:
            return None
        try:
            clean_str = date_str.strip().replace('Z', '+00:00')
            return datetime.fromisoformat(clean_str).replace(tzinfo=None)
        except Exception:
            return None

    def cargar_datos(self) -> None:
        self._cache = {}
        self._cache_email = {}
        self._cache_upn = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de Entra ID configurado en: {self.path_file}")
            return

        try:
            #df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df = pd.read_csv(self.path_file, sep=";").fillna('')

            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                id_user = str(row.get('ID', '')).strip().upper()
                if not id_user or id_user == 'NAN':
                    continue

                last_sign_in = ""
                last_non_interactive = ""

                sign_in_activity_raw = row.get('SIGNINACTIVITY', '')
                if sign_in_activity_raw:
                    try:
                        if isinstance(sign_in_activity_raw, str):
                            data_json = json.loads(sign_in_activity_raw)
                        else:
                            data_json = sign_in_activity_raw
                        
                        last_sign_in = data_json.get('lastSignInDateTime', '') or ""
                        last_non_interactive = data_json.get('lastNonInteractiveSignInDateTime', '') or ""
                    except Exception:
                        pass

                dt_interactive = self._parse_datetime(last_sign_in)
                dt_non_interactive = self._parse_datetime(last_non_interactive)

                if dt_interactive and dt_non_interactive:
                    last_activity = dt_interactive if dt_interactive >= dt_non_interactive else dt_non_interactive
                elif dt_interactive:
                    last_activity = dt_interactive
                elif dt_non_interactive:
                    last_activity = dt_non_interactive
                else:
                    last_activity = None

                raw_id = str(row.get('ID', '')).strip()
                raw_upn = str(row.get('USERPRINCIPALNAME', '')).strip()
                raw_email = str(row.get('MAIL', '')).strip()

                user_obj = EntraUser(
                    id = raw_id,
                    upn = raw_upn,
                    email = raw_email,
                    isActive = str(row.get('ACCOUNTENABLED', '')).strip().upper() in ["TRUE", "VERDADERO", "1"],
                    fechaCreacion = to_datetime(str(row.get('CREATEDDATETIME', '')).strip(),"MDA"),
                    lastSignInDateTime = dt_interactive,
                    lastNonInteractiveSignInDateTime = dt_non_interactive,
                    lastActivityDateTime = last_activity,
                    dni = str(row.get("FAXNUMBER", '')).strip(),
                    rol = str(row.get('POSTALCODE', '')).strip(),
                    jefe = str(row.get('STREETADDRESS', '')).strip()
                )

                self._cache[id_user] = user_obj
                
                if raw_email:
                    self._cache_email[raw_email.upper()] = user_obj
                if raw_upn:
                    self._cache_upn[raw_upn.upper()] = user_obj

            print(f"Entra Id ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def delete_file(self) -> bool:
        delete_file(self.path_file)
        self._cache.clear()
        self._cache_email.clear()
        self._cache_upn.clear()
        return True

    def get_by_email(self, email: str) -> EntraUser | None:
        if not email:
            return None
        return self._cache_email.get(email.strip().upper())
    
    def get_by_upn(self, upn: str) -> EntraUser | None:
        if not upn:
            return None
        return self._cache_upn.get(upn.strip().upper())
    
    def get_all(self) -> list[EntraUser]:
        return list(self._cache.values())
    