import pandas as pd
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from models.file_names import FileName
from logic.share.utils import to_datetime, delete_file

load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

@dataclass
class EasUser:
    user_id: str = ""
    nombre_completo: str = ""
    grupo_id: str = ""
    fecha_expiracion: str = ""
    cuenta_autenticacion: str = ""
    fecha_expiracion_pass: str = ""
    fecha_login: str = ""
    isActive: bool = False
    app_name: str = ""

class EasUserService():
    def __init__(self, lazy:bool = False):
        self._cache: dict[str, EasUser] = {}
        self.folder_path = DATA_PATH
        
        self.file_enum: FileName = FileName.EAS

        nombre_archivo = self.file_enum.value
        self.path_file = os.path.join(self.folder_path, nombre_archivo)

        if not lazy:
            self.cargar_datos()

    def cargar_datos(self) -> None:
        self._cache = {}

        if not self.path_file or not os.path.exists(self.path_file):
            print(f"Error: No se encontró el archivo de EAS configurado en: {self.path_file}")
            return

        try:
            df = pd.read_parquet(self.path_file, engine='pyarrow').fillna('')
            df.columns = [str(c).strip().upper() for c in df.columns]

            for _, row in df.iterrows():
                user_id = str(row.get('USER_ID', '')).strip().upper()
                if not user_id or user_id == 'NAN': 
                    continue
                
                self._cache[user_id] = EasUser(
                    user_id=str(row.get('USER_ID', '')).strip(),
                    nombre_completo=str(row.get('USER_NAME', '')).strip(),
                    grupo_id=str(row.get('GROUP_ID', '')).strip(),
                    fecha_expiracion=str(row.get('FECHAEXPIRACION_CUENTA', '')).strip(),
                    cuenta_autenticacion=str(row.get('CUENTAAUTENTICACION_WINDOWS', '')).strip(),
                    fecha_expiracion_pass=str(row.get('FECHAEXPIRACION_PASSWORD', '')).strip(),
                    fecha_login=str(row.get('FECHAULTIMOLOGIN', '')).strip(),
                    isActive=not str(row.get('INDICADORBLOQUEADO', '')).strip().upper() in ['Y', 'YES', 'TRUE', '1'],
                    app_name="EAS",
                )

            print(f"App EAS ({self.file_enum.name}) | Total en cache: {len(self._cache)}")

        except Exception as e:
            print(f"Error cargando datos desde {self.path_file}: {e}")

    def get_all(self) -> list[EasUser]:
        return list(self._cache.values())